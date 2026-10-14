#!/usr/bin/env python3
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

class JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.blocks = []
        self.active = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.blocks.append({'id': attrs.get('id'), 'text': ''})
            self.active = self.blocks[-1]

    def handle_data(self, data):
        if self.active is not None:
            self.active['text'] += data

    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = None

parser = argparse.ArgumentParser()
source = parser.add_mutually_exclusive_group(required=True)
source.add_argument('--file')
source.add_argument('--url')
args = parser.parse_args()
if args.file:
    document = Path(args.file).read_text(encoding='utf-8')
else:
    with urlopen(Request(args.url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as response:
        if response.status != 200:
            raise SystemExit('FAIL: target page must return HTTP 200')
        document = response.read().decode('utf-8')
html = JsonLdParser()
html.feed(document)
blocks = [block for block in html.blocks if block['id'] == 'newsroom-jsonld']
if len(blocks) != 1:
    raise SystemExit(f'FAIL: expected one native newsroom-jsonld script, found {len(blocks)}')
value = json.loads(blocks[0]['text'])
graph = value['@graph']
if value.get('@context') != 'https://schema.org':
    raise SystemExit('FAIL: incorrect schema context')
pages = [node for node in graph if node.get('@type') == 'CollectionPage']
if len(pages) != 1:
    raise SystemExit('FAIL: expected one CollectionPage')
breadcrumbs = [node for node in graph if node.get('@type') == 'BreadcrumbList']
if len(breadcrumbs) != 1:
    raise SystemExit('FAIL: expected one BreadcrumbList')
crumbs = breadcrumbs[0]['itemListElement']
if [(item['position'], item['name']) for item in crumbs] != [(1, 'Home'), (2, 'Newsroom')]:
    raise SystemExit('FAIL: expected Home → Newsroom')
if crumbs[1]['item'] != pages[0]['url'] or pages[0].get('breadcrumb', {}).get('@id') != breadcrumbs[0]['@id']:
    raise SystemExit('FAIL: breadcrumb page/reference mismatch')
sites = [node for node in graph if node.get('@type') == 'WebSite']
if len(sites) != 1 or pages[0].get('isPartOf', {}).get('@id') != sites[0]['@id']:
    raise SystemExit('FAIL: WebSite/page relationship mismatch')
images = [node for node in graph if node.get('@type') == 'ImageObject']
for image in images:
    if image.get('encodingFormat') != 'image/svg+xml' or image.get('isPartOf', {}).get('@id') != pages[0]['@id']:
        raise SystemExit('FAIL: brand asset format/page mismatch')
lists = [node for node in graph if node.get('@type') == 'ItemList']
for listing in lists:
    items = listing['itemListElement']
    if listing['numberOfItems'] != len(items):
        raise SystemExit('FAIL: numberOfItems mismatch')
    if [item['position'] for item in items] != list(range(1, len(items) + 1)):
        raise SystemExit('FAIL: incorrect list positions')
print(json.dumps({'native_script_count': 1, 'page_type': 'CollectionPage', 'page_url': pages[0]['url'], 'list_sizes': [len(node['itemListElement']) for node in lists], 'scope': 'Response JSON-LD only; visible-content matching and indexability still require separate checks'}, ensure_ascii=False, indent=2))

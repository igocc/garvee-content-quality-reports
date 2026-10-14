import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { buildNewsroomJsonLd, serializeJsonLd } from './newsroom-structured-data.mjs';

const content = JSON.parse(await readFile(new URL('./newsroom-data.json', import.meta.url), 'utf8'));
const organization = {
  homeUrl: 'https://garvee.com/en',
  organizationUrl: 'https://www.garvee.com/',
  organizationId: 'https://www.garvee.com/#organization',
  websiteUrl: 'https://www.garvee.com/',
  websiteId: 'https://www.garvee.com/#website',
};
const brandAsset = JSON.parse(await readFile(new URL('./newsroom-brand-asset.preview.json', import.meta.url), 'utf8'));
const preview = buildNewsroomJsonLd({
  pageUrl: 'https://a67y76j.garvee.com/pages/news-room', ...organization, ...content,
  brandAsset,
});
const productionExample = buildNewsroomJsonLd({
  pageUrl: 'https://www.garvee.com/pages/news-room', ...organization, ...content,
});
const minimal = buildNewsroomJsonLd({
  pageUrl: 'https://a67y76j.garvee.com/pages/news-room', ...organization, ...content,
  includeLists: false,
});
assert.equal(minimal['@graph'].length, 5);
assert.ok(!minimal['@graph'].some(node => node['@type'] === 'ItemList'));

const ids = new Set(preview['@graph'].map(node => node['@id']));
function checkReferences(value) {
  if (Array.isArray(value)) return value.forEach(checkReferences);
  if (!value || typeof value !== 'object') return;
  if (Object.keys(value).length === 1 && value['@id']) assert.ok(ids.has(value['@id']));
  Object.values(value).forEach(checkReferences);
}
checkReferences(preview);
const pageEntity = preview['@graph'].find(node => node['@type'] === 'CollectionPage');
assert.equal(pageEntity.isPartOf['@id'], organization.websiteId);
const asset = preview['@graph'].find(node => node['@type'] === 'ImageObject');
assert.equal(asset.contentUrl, brandAsset.url);
assert.equal(asset.encodingFormat, 'image/svg+xml');
assert.equal(pageEntity.hasPart['@id'], asset['@id']);
assert.equal(asset.isPartOf['@id'], pageEntity['@id']);
assert.ok(!productionExample['@graph'].some(node => node['@type'] === 'ImageObject'));
assert.ok(!JSON.stringify(productionExample).includes('a67y76j.garvee.com'));
assert.throws(() => buildNewsroomJsonLd({ pageUrl: 'https://a67y76j.garvee.com/pages/news-room', ...organization, ...content, websiteUrl: 'https://garvee.com/en' }));
const breadcrumb = preview['@graph'].find(node => node['@type'] === 'BreadcrumbList');
assert.deepEqual(breadcrumb.itemListElement.map(item => [item.position, item.name, item.item]), [
  [1, 'Home', organization.homeUrl],
  [2, 'Newsroom', 'https://a67y76j.garvee.com/pages/news-room'],
]);
assert.equal(preview['@graph'].find(node => node['@type'] === 'CollectionPage').breadcrumb['@id'], breadcrumb['@id']);
assert.throws(() => buildNewsroomJsonLd({ pageUrl: organization.homeUrl, ...organization, ...content }));
const lists = preview['@graph'].filter(node => node['@type'] === 'ItemList');
assert.deepEqual(lists.map(node => node.numberOfItems), [3, 3]);
for (const list of lists) {
  assert.deepEqual(list.itemListElement.map(item => item.position), [1, 2, 3]);
  assert.equal(new Set(list.itemListElement.map(item => item.url)).size, 3);
  assert.ok(list.itemListElement.every(item => !item.name.includes('\\n')));
}
const hostileContent = { ...content, pressReleases: [{ ...content.pressReleases[0], title: '</script><script>alert(1)</script>' }] };
const hostile = buildNewsroomJsonLd({ pageUrl: 'https://a67y76j.garvee.com/pages/news-room', ...organization, ...hostileContent });
assert.ok(!serializeJsonLd(hostile).includes('<'));
assert.deepEqual(JSON.parse(serializeJsonLd(hostile)), hostile);
assert.throws(() => buildNewsroomJsonLd({ pageUrl: 'https://a67y76j.garvee.com/pages/news-room', ...organization, ...content, pressReleases: [content.pressReleases[0], content.pressReleases[0]] }));
assert.throws(() => buildNewsroomJsonLd({ pageUrl: 'https://a67y76j.garvee.com/pages/news-room?utm_source=x', ...organization, ...content }));
const empty = buildNewsroomJsonLd({ pageUrl: 'https://a67y76j.garvee.com/pages/news-room', ...organization, pressReleases: [], mediaCoverage: [] });
assert.ok(!empty['@graph'].some(node => node['@type'] === 'ItemList'));
assert.ok(empty['@graph'].some(node => node['@type'] === 'BreadcrumbList'));
const fourReleases = buildNewsroomJsonLd({
  pageUrl: 'https://a67y76j.garvee.com/pages/news-room', ...organization, ...content,
  pressReleases: [...content.pressReleases, { title: 'Additional visible release', url: 'https://example.org/new-release' }],
});
const expandedList = fourReleases['@graph'].find(node => node['@type'] === 'ItemList');
assert.equal(expandedList.numberOfItems, 4);
assert.deepEqual(expandedList.itemListElement.map(item => item.position), [1, 2, 3, 4]);

await writeFile(new URL('./newsroom-schema.minimal-preview.json', import.meta.url), JSON.stringify(minimal, null, 2));
await writeFile(new URL('./newsroom-schema.minimal-preview.html', import.meta.url), `<script id="newsroom-jsonld" type="application/ld+json">${serializeJsonLd(minimal)}</script>\n`);
await writeFile(new URL('./newsroom-schema.preview.json', import.meta.url), JSON.stringify(preview, null, 2));
await writeFile(new URL('./newsroom-schema.production-example.json', import.meta.url), JSON.stringify(productionExample, null, 2));
await writeFile(new URL('./newsroom-schema.preview.html', import.meta.url), `<script id="newsroom-jsonld" type="application/ld+json">${serializeJsonLd(preview)}</script>\n`);
const homepageSchema = {
  '@context': 'https://schema.org',
  '@graph': preview['@graph'].filter(node => ['Organization', 'ContactPoint', 'WebSite'].includes(node['@type'])),
};
await writeFile(new URL('./website-homepage.example.json', import.meta.url), JSON.stringify(homepageSchema, null, 2));
await writeFile(new URL('./website-homepage.example.html', import.meta.url), `<script type="application/ld+json">${serializeJsonLd(homepageSchema)}</script>\n`);
console.log(JSON.stringify({ graphNodes: preview['@graph'].length, minimalNodes: minimal['@graph'].length, visibleListSizes: lists.map(node => node.numberOfItems), websiteAndAsset: 'pass', productionAsset: 'omitted until verified', breadcrumb: 'Home → Newsroom', dynamicListLength: 'pass (3 → 4)', references: 'pass', serialization: 'pass', duplicateHandling: 'pass', queryUrlHandling: 'pass', emptyLists: 'pass', deployed: false }, null, 2));

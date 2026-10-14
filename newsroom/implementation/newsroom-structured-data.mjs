export function normalizeTitle(value) {
  return String(value).replace(/\\[nr]/g, ' ').replace(/\s+/g, ' ').trim();
}

function absoluteHttps(value, label) {
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password) {
    throw new Error(`${label} must be an absolute HTTPS URL without credentials`);
  }
  return url.href;
}

function buildList(pageUrl, fragment, name, entries) {
  if (entries.length === 0) return null;
  const seen = new Set();
  const items = entries.map((entry, index) => {
    const title = normalizeTitle(entry.title);
    const url = absoluteHttps(entry.url, 'entry.url');
    if (!title) throw new Error('A visible entry must have a title');
    if (seen.has(url)) throw new Error(`Duplicate URL in ${fragment}: ${url}`);
    seen.add(url);
    return { '@type': 'ListItem', position: index + 1, name: title, url };
  });
  return {
    '@type': 'ItemList', '@id': `${pageUrl}#${fragment}`, name,
    numberOfItems: items.length, itemListElement: items,
  };
}

export function buildNewsroomBreadcrumb({ homeUrl, pageUrl }) {
  const home = new URL(absoluteHttps(homeUrl, 'homeUrl'));
  const page = new URL(absoluteHttps(pageUrl, 'pageUrl'));
  if (home.search || home.hash || page.search || page.hash) {
    throw new Error('Breadcrumb URLs must not contain query or fragment');
  }
  if (home.href === page.href) throw new Error('Home and Newsroom must have distinct URLs');
  return {
    '@type': 'BreadcrumbList', '@id': `${page.href}#breadcrumb`,
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: home.href },
      { '@type': 'ListItem', position: 2, name: 'Newsroom', item: page.href },
    ],
  };
}

export function buildNewsroomJsonLd({
  homeUrl, pageUrl, organizationUrl, organizationId, pressReleases, mediaCoverage,
  websiteUrl, websiteId, brandAsset,
  includeLists = true,
}) {
  const page = new URL(absoluteHttps(pageUrl, 'pageUrl'));
  if (page.search || page.hash) throw new Error('pageUrl must not contain query or fragment');
  const pageAddress = page.href;
  const organizationAddress = absoluteHttps(organizationUrl, 'organizationUrl');
  const organizationIdentity = absoluteHttps(organizationId, 'organizationId');
  const contactId = `${organizationIdentity.split('#')[0]}#press-contact`;
  const siteAddress = new URL(absoluteHttps(websiteUrl, 'websiteUrl'));
  if (siteAddress.pathname !== '/' || siteAddress.search || siteAddress.hash) {
    throw new Error('websiteUrl must be the domain or subdomain root');
  }
  const siteIdentity = absoluteHttps(websiteId, 'websiteId');
  const site = {
    '@type': 'WebSite', '@id': siteIdentity,
    name: 'GARVEE', url: siteAddress.href,
    publisher: { '@id': organizationIdentity },
  };
  let asset;
  if (brandAsset) {
    const title = normalizeTitle(brandAsset.title);
    if (!title) throw new Error('The visible brand asset must have a title');
    asset = {
      '@type': 'ImageObject', '@id': `${pageAddress}#brand-wordmark`,
      name: title, contentUrl: absoluteHttps(brandAsset.url, 'brandAsset.url'),
      encodingFormat: 'image/svg+xml',
      isPartOf: { '@id': `${pageAddress}#webpage` },
    };
  }
  const breadcrumb = buildNewsroomBreadcrumb({ homeUrl, pageUrl: pageAddress });
  const lists = includeLists ? [
    buildList(pageAddress, 'news', 'GARVEE press releases', pressReleases),
    buildList(pageAddress, 'coverage', 'GARVEE media coverage', mediaCoverage),
  ].filter(Boolean) : [];
  const webPage = {
    '@type': 'CollectionPage', '@id': `${pageAddress}#webpage`,
    url: pageAddress, name: 'GARVEE Newsroom', inLanguage: 'en',
    about: { '@id': organizationIdentity },
    publisher: { '@id': organizationIdentity },
    isPartOf: { '@id': siteIdentity },
    breadcrumb: { '@id': breadcrumb['@id'] },
  };
  if (asset) webPage.hasPart = { '@id': asset['@id'] };
  if (lists.length) webPage.mainEntity = lists.map(item => ({ '@id': item['@id'] }));
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Organization', '@id': organizationIdentity,
        name: 'GARVEE', url: organizationAddress,
        contactPoint: { '@id': contactId },
      },
      {
        '@type': 'ContactPoint', '@id': contactId,
        contactType: 'press inquiries', email: 'branding@garvee.com',
      },
      site, webPage, breadcrumb, ...lists, ...(asset ? [asset] : []),
    ],
  };
}

export function serializeJsonLd(value) {
  // JSON-LD must remain data even when a CMS title contains an HTML closing tag.
  return JSON.stringify(value).replace(/</g, '\\u003c');
}

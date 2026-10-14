# GARVEE Newsroom 结构化数据实施方案

本包为参考实现，未修改线上网站。

## 1. 完整方案：8 个实体

- `Organization`：GARVEE，复用主站统一 `@id`。
- `WebSite`：GARVEE 主站，与 CollectionPage.isPartOf 关联；复用全站 @id。
- `ContactPoint`：`branding@garvee.com`，`press inquiries`。
- `CollectionPage`：新闻室页面；`breadcrumb` 引用面包屑。
- `BreadcrumbList`：Home → Newsroom，同时在页面显示可见导航。

- 两个 `ItemList`：当前页面两组真实展示条目，数量动态生成。
- `ImageObject`：当前可下载的 GARVEE wordmark SVG，以 CollectionPage.hasPart 关联，contentUrl 指向实际文件。

本次按“全部适用类型”纳入以上 8 个实体。`newsroom-schema.preview.json/html` 为完整预览样例；`newsroom-schema.minimal-preview.json/html` 为不含列表与资源详情的 5 实体基础版。两组报道的 `ItemList` 是可选项，不是新闻室必须添加的标记。JSON-LD 也不是索引或排名的必需条件。

## 2. 为什么完整样例是 3＋3

审查快照中，新闻稿区实际展示 3 篇，媒体报道区实际展示 3 篇，所以完整样例各含 3 条。

不是数量上限，也不是固定 SEO 规则。完整列表版由实际展示数组生成 `name/url/position`；`numberOfItems` 自动计算。变成 4 条就输出 4 条。Logo、副本、Read story 重复入口不增加条目；重点报道与媒体卡片重复的文章只计一次。

`newsroom-data.json` 是快照输入；工程集成时使用现有展示数组，不维护第二套文章数据。标题先用 `normalizeTitle` 清理；UI 与 Schema 使用同一结果。

## 3. 服务端集成

```jsx
import NewsroomJsonLd from './NewsroomJsonLd.jsx';
import NewsroomBreadcrumb from './NewsroomBreadcrumb.jsx';

const urls = {
  homeUrl: siteConfig.homeUrl,
  pageUrl: siteConfig.newsroomUrl,
  organizationUrl: siteConfig.organizationUrl,
  organizationId: siteConfig.organizationId,
  websiteUrl: siteConfig.websiteUrl,
  websiteId: siteConfig.websiteId,
};

// 仅放在 news-room 路由的 Server page/layout 中。
<>
  <NewsroomJsonLd {...urls}
    includeLists={true}
    brandAsset={verifiedVisibleBrandAsset}
    pressReleases={displayedPressReleases}
    mediaCoverage={displayedMediaCoverage}
  />
  <NewsroomBreadcrumb homeUrl={urls.homeUrl} pageUrl={urls.pageUrl} />
  {/* 原有新闻室内容 */}
</>
```

默认启用完整列表版；若只需基础版，设置 includeLists=false 且不传 brandAsset。不要同时输出精简与完整两份 script。

导航样式：

```css
.newsroom-breadcrumb {
  display: flex;
  gap: .5rem;
  list-style: none;
  margin: 0;
  padding: 0;
}
```

Home 是真实首页链接；Newsroom 是当前页文本，带 `aria-current="page"`。HTML 和 JSON-LD 共用生成函数及 URL 配置。站内 Home 链接无需 nofollow。

## 4. URL 与字段规则

- `homeUrl`：真实首页规范地址。按用户当前要求统一为 `https://garvee.com/`，HTML 导航和 BreadcrumbList 使用同一地址。
- `pageUrl`：预览样例为 `https://a67y76j.garvee.com/pages/news-room`；正式版替换为返回 200 的唯一 newsroom 地址，与 canonical/og:url/sitemap 一致。
- `websiteUrl/websiteId`：WebSite.url 使用主域或子域根地址，不能把 /en 当作单独网站；样例为 https://www.garvee.com/ 与 #website。正式发布时同步核验首页 canonical 与根域配置；本样例不承诺 Google 网站名称展示资格。
- 主站已有 WebSite 时复用 @id。Google 网站名称标记须部署在域名/子域根首页；仅新闻室新增不能替代首页标记。website-homepage.example.json/html 提供根首页候选片段，合并已有实体，禁止重复创建。新闻室的 isPartOf 引用同一 WebSite。
- `brandAsset`：仅传页面实际可见、已验证为 SVG 的 {title,url}。本次预览资源复查 200、image/svg+xml；正式同路径 404。因此生产样例暂不生成 ImageObject；先发布稳定正式资产，确认 200 且 HTML 下载链接一致，再传入。不要把预览文件地址带进正式图谱。
- `organizationUrl/organizationId`：样例为 www 主域与 `#organization`；这是参考配置，不是已检测到的既存实体。根布局已有组织时复用并合并 contactPoint，不覆盖客服等信息。
- `BreadcrumbList.@id`：`pageUrl + #breadcrumb`；位置 1 Home、位置 2 Newsroom，`item` 与可见导航地址一致。
- 不填未经核实的 author、日期、legalName、电话、地址、评分、奖项或媒体 sameAs。Logo 待稳定正式资产返回 200 后再填。

组件不加 `use client`；原生 JSON-LD script 在首次响应出现，不使用 useEffect/GTM/afterInteractive。JSON 字符串中的 `<` 转义为 `\u003c`。JSON-LD 不能修复 hidden 正文或解除 robots 保护。

## 5. 验收

```bash
node generate-and-check.mjs
python3 verify-response.py --file newsroom-schema.minimal-preview.html
python3 verify-response.py --file newsroom-schema.preview.html
# 集成后检查真实响应
python3 verify-response.py --url https://a67y76j.garvee.com/pages/news-room
```

本地已检查：网站和页面引用、品牌资源的 hasPart/isPartOf、生产候选无预览域、根域校验、基础版 5 实体、完整预览版 8 实体、无正式资产的生产候选 7 实体、Home → Newsroom 引用、列表数量动态变化（3 → 4）、安全序列化、重复 URL、空列表、参数 URL、离线响应解析。

上线另验：可见面包屑与 Schema 一致；无 JS 仍能读正文；唯一 main；外部 a 全部 nofollow；正式页 200 且允许抓取；Schema.org Validator、Google Rich Results Test、Search Console URL Inspection。尚未运行组件工程、远程部署或在线验证。

[Google BreadcrumbList](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb) · [Next.js JSON-LD](https://nextjs.org/docs/app/guides/json-ld)

## 6. 类型边界

CollectionPage 已是 WebPage 子类型，不再复制一份同 URL 的 WebPage。本站没有对应全文、问答、视频、活动、岗位、价格、评分，不添加 NewsArticle/FAQPage/VideoObject/Event/JobPosting/Product/Offer/Review/AggregateRating。媒体 Logo 不是奖项或 GARVEE.sameAs。

若以后新增真实内容，再按内容匹配类型；不要按“支持类型清单”逐项堆砌。Organization.logo、官方社交 sameAs、法律主体和电话等只在正式地址与事实核验后填入。本次没有这些已核实生产配置，未虚构。

[Google 网站名称与根首页部署](https://developers.google.com/search/docs/appearance/site-names) · [WebSite](https://schema.org/WebSite) · [ImageObject](https://schema.org/ImageObject) · [hasPart](https://schema.org/hasPart)

## 7. Newsroom JS 精简

用户范围：第三方只保留基础访问统计与必要监控，营销代码不进入新闻室。详细配置与触发证据见 newsroom-js-optimization.md、newsroom-js-audit-summary.json。

从页面布局停止 Klaviyo/Convbox initializer、客户识别、冗余商城 analytics 和商店徽章；Web GTM 逐事件排除营销标签及序列依赖；sGTM 保留 Analytics 转发并阻止该页面的营销目的地。未取得应用源码及 GTM/sGTM 管理端，交付为已核查的实施规格，未执行线上删除。

## 8. HTML 列表语义

newsroom-list-markup.html 为可复制的 HTML 片段，含 3 条新闻稿、3 条媒体卡片与 Home → Newsroom 面包屑，不是完整新闻室页面。

- 新闻稿、媒体卡片是并列条目，使用 ul > li；按日期倒序展示不必强改成 ol。
- 面包屑体现导航层级，使用 nav > ol > li，当前页 aria-current=page；与 BreadcrumbList 顺序一致。
- ul/ol 的直接条目用 li，不用 div 包裹 li；H3/a/time/p 放在 li 内。
- 保留原有 grid 类并重置列表默认样式；隐藏项目符号的 ul 显式保留 role=list。
- 单个 Featured 摘要可保留 article；纯布局 div 不机械改成列表。
- 真实外部链接包含 nofollow；图片、下载等资源不因列表标记自动生成 Schema。
- 片段内容应由页面展示数组动态生成；若启用 ItemList，两组 HTML 与 Schema 的标题、URL、数量、顺序必须一致。

这项改善语义和可访问性，不承诺排名提升；已生成本地参考并更新报告，未修改 GARVEE 线上源码。

## 9. 完整元数据代码

`newsroom-meta.html` 已合并 title、description、OG/X 文字、首页真实图片地址、width=1200、height=675、alt 与 favicon。

使用此完整文件；不重复追加 `newsroom-image-meta.html` 的同名标签。canonical/og:url 按正式新闻室地址配置。

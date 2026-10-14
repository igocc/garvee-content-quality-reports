# Newsroom JS 精简：只保留统计与必要监控

审查日期：2026-10-14。只读审查与本地参考方案，未修改 GARVEE 网站或 GTM/sGTM 配置。

## 1. 已确认触发来源

| 请求／SDK | 触发来源 | Newsroom 处理 |
| --- | --- | --- |
| `/cart.js` | Web GTM tag_id=135 在 gtm.js 触发 YutoAds → check-cart.js → check_cart；已发布规则没有该标签的 block exception | 对新闻室排除 tag 135，并停用所有购物车营销探测；不能只屏蔽 API |
| Klaviyo Onsite／forms／Atlas／reviews | 页面原生 `klaviyo-init` 立即 appendChild；仅按 bot UA 跳过，不检查路由 | 服务端不输出此 initializer，不加载 SDK；只在 Klaviyo 后台隐藏弹窗仍会下载大量模块 |
| Convbox Omnitrack | 页面原生 `convbox-init`：首次 scroll/mousemove/touch/key/click，或 2000ms 兜底自动加载 | 新闻室不输出队列/init、监听与 timer，不加载 SDK 或 bridge/pixels；“延后 2 秒”不是删除 |
| AddShoppers／Shop.pe | Web GTM tag_id=218 在 gtm.js 触发，无该标签 block exception；随后加载 widget 与 datapartners/status | 排除标签与所有关联 setup/cleanup 标签 |
| TriplePixel／config-security | Web GTM tag_id=234 在 gtm.init 触发，无该标签 block exception；237 在 page_view 且路径不含 collections/products/search/cart 时触发，新闻室也满足 | 初始化和事件标签统一排除新闻室，不只删初始化标签 |
| Meta／TikTok／Bing／Taboola／RTB／Upsellit 等 | 实测加载广告与再营销脚本；Upsellit tag_id=211 也由 gtm.js 触发 | 广告、再营销、联盟与转化营销标签全部排除；不归入保留统计代码 |
| `/api/internal/customer` | 站点 chunk 2381：SWR revalidateOnMount=true，读取后写 __customerEmail／__garveeCustomerId | 新闻室不挂载此客户识别组件；如复用 hook，用 null SWR key 停止请求，避免条件调用 hook |
| `/api/unstable/graphql.json` | 站点 chunk 995 的 Shopify query ensureCookies / consentManagement；不是购物车查询 | 新闻室停用 Shopify 商城 analytics provider 时一并移除其 cookie 初始化；保留真正的 Consent/CMP 能力，不全站封禁 GraphQL |
| Shopify monorail | 实测商城 page-view 遥测 | 新闻室以 GA4 为基础统计，不加载冗余商城 analytics provider；对其它商城路由保持现有逻辑 |
| merchantwidget.js／Google 商店品质 iframe | 站点 chunk 5529 的 useEffect 直接加载，未经过 GTM | 新闻室不挂载 merchant badge 组件 |
| GA4／`metrics.garvee.com/g/collect` | GTM Google tag 配置 server_container_url=metrics.garvee.com；同时看到 analytics.google.com/g/collect | 保留一条明确 GA4 统计链路；用 Tag Assistant / DebugView 核对 measurement ID 与事件，不仅凭两个 collect 域名就判重复 |
| `/api/internal/logger` | 站点自身观测模块 | 保留错误/CWV 监控；停止检查已经禁止的 SDK，避免产生“加载失败”重试与噪音日志 |

## 2. 最小保留范围

- 必要的页面交互、同意管理、GA4 访问统计、错误与 Web Vitals 监控。
- 统计事件：page_view、media_coverage_click、press_release_click、brand_asset_download、media_contact_click；不发送商品/购物车事件，不查询用户 email/customerId 供营销。
- 不加载广告像素、再营销、联盟、弹窗、推荐、客户识别、商店徽章和营销归因 SDK。Clarity 等会话回放默认也不加载，若以后需要另行启用。

## 3. 三处改动

**页面／布局**：服务端按 news-room slug 停止输出 Klaviyo/Convbox initializer；停止挂载 customer identification、Shopify commerce analytics、merchant badge。保留统计与必要 UI。把初始化入口排除掉，不能只隐藏弹窗或等待 SDK 加载后卸载。

**Web GTM**：在容器加载前提供 page_type。营销标签全部增加新闻室 exception，覆盖 gtm.init、gtm.js、page_view、自定义事件与历史路由变化；检查 Tag Sequencing 是否绕过触发器。不要删 GA4/Consent/CWV 统计标签。

```html
<script>
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({
  page_type: 'newsroom',
  marketing_enabled: false
});
</script>
```

以上由服务端仅在新闻室输出，先于现有 GTM bootstrap。Web GTM 建 Data Layer Variable `page_type`；按相同事件类型建立 exception，条件 `page_type equals newsroom`。例如 Yuto/Shop.pe 的 exception 用 Page View，Triple 初始化用 Initialization；自定义 page_view 标签用同名 Custom Event exception。检查并解除统计标签对营销 setup/cleanup 标签的依赖；被序列调用的 Custom HTML 必须在代码内部检查当前 page_type 并拒绝加载营销 SDK。不能依赖附属标签自己的触发器，因为 Tag Sequencing 可绕过它。

页面路径兜底匹配已核验的两种路径：`^/(?:en/)?pages/news-room/?$`。其它语言前缀按站点实际 locale 列表补充。SPA 路由切换必须先同步 page_type 再发送统计事件；已经加载的营销 SDK 不能靠设置 flag 自动撤销，新闻室入口须使用不会继承营销 SDK 的隔离布局或完整页面导航。

**sGTM**：保持 GA4 analytics 转发；对 page_type=newsroom 的事件排除 Google Ads、Meta、其它广告与营销目的地。确认该参数映射为服务端事件字段后，按该字段配置过滤/触发条件。此处管理端配置未取得，不能声称已验证或已修改服务端规则。

服务端容器不能撤销浏览器已经下载执行的 Custom HTML／SDK。客户端停止加载与服务端停止营销转发必须同时处理。[Google sGTM](https://developers.google.com/tag-platform/tag-manager/server-side/overview)、[GTM exceptions 与 Tag Sequencing](https://support.google.com/tagmanager/answer/7679318?hl=en)。

## 4. 验收与实测

基线为一次 18 秒重新加载、浏览器缓存禁用、未主动点击。剔除扩展与非正常 HTTP 地址后：197 个网站请求，124 个 Script 请求；Klaviyo 家族 51 个请求，其中 43 个脚本请求。不是整个网站固定数量，也不是 Lighthouse/CWV 分数。

隔离实验只在审计浏览器阻止 metrics.garvee.com/gtm.js：`/cart.js` 从 1 次变 0；ensureCookies GraphQL 与 customer 请求仍各 1 次；Klaviyo 仍 51 次，merchantwidget 仍 1 次。正文 H1 仍可读。证明这几组入口需要分别处理；不是完整精简方案已经上线的性能收益。

上线验收：

1. 首次加载与停留超过 2 秒、点击/滚动后，均不出现上述禁止的 SDK、cart.js、customer identification、merchant widget 或营销桥接请求。
2. GA4 page_view 保持一次，点击/下载事件正常；Web 与 Server 两侧 Tag Assistant 检查营销标签未触发。
3. 客户/购物车数据不在 GA4 payload；Consent/CMP 仍正常，日志不为禁用 SDK 重试。
4. 内部导航到新闻室也不继承营销 SDK；新闻室与商城路由分别检查，不影响商城。
5. 无 JS 正文、元数据、canonical、JSON-LD 仍在响应可读；用同环境前后对比请求数、JS 传输量、主线程长任务与 CWV。不承诺具体提速比例。

公开证据只包含精简请求/触发摘要，不发布原始请求参数、用户标识、浏览器扩展、完整 GTM 配置或本机路径。

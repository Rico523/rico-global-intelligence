# 来源与第三方数据

本项目用途为个人、非商业 RSS 阅读与原文导航。发布者保留内容版权；来源连通测试不能证明公开再分发获得授权。网站展示署名与原文链接，没有全文、摘要、图片、广告或付费功能。

- BBC News：[RSS 说明](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm)。BBC 的 RSS/元数据条款要求署名与附近链接，并对更改 feed、品牌以及商业使用作限制；上线前应检查当前 [BBC 使用条款](https://www.bbc.co.uk/usingthebbc/terms/)，不要将本项目视为已取得商业元数据许可。
- The Guardian：[RSS 使用说明](https://www.theguardian.com/help/feeds)、[公开许可条件](https://www.theguardian.com/info/2022/nov/01/open-licence-terms)。本项目限制为个人非商业用途，并为每条标题提供来源与原文链接。
- Al Jazeera：[官网](https://www.aljazeera.com/)、[条款](https://www.aljazeera.com/terms-and-conditions)。公开 RSS 为读取入口，不自动赋予其他用途的许可。
- DW：[官网](https://www.dw.com/)。使用其公开 RSS，不绕过访问限制；公开发布前复核其版权和当前使用条件。
- CNA Singapore：本次云端再测 robots 仍禁止，已从启用配置移除。与台湾中央通訊社不同，不影响中央通訊社 RSS。
- Khmer Times：本地可访问，GitHub 运行器 robots 返回 403，两个 Feed 已从启用配置移除。
- NASA：因第二次云端运行返回 429 限流而已从正式启用列表移除，不重试或绕过限制。
- Euronews：[官网](https://www.euronews.com/)。仅公开 RSS 标题与原文导航；公开发布前复核当前条款。

若发布者不允许所需公开使用，应移除该订阅并替换免费允许的公开来源；不购买许可或绕过技术限制。robots.txt 是访问规则检查，不是内容版权授权。网站已作为个人非商业标题阅读器发布；若来源政策变化导致不适用，将移除该来源，不购买许可。

## 海岸线

`site/assets/land.json` 来自 Natural Earth 的 `ne_110m_land`，保留每个多边形外环并将经纬度四舍五入至三位小数，无国界。

- [数据来源](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson)
- [Natural Earth 公共领域使用条款](https://www.naturalearthdata.com/about/terms-of-use/)

数据随项目保存，浏览器不连接地图服务，无 API Key，无地图计费。文件约 85 KB；无需持续下载更新。


## 本次扩源边界

- 中央通訊社：采用[官方 RSS 目录](https://www.cna.com.tw/about/rss.aspx)中公布的 FeedBurner 地址。个人非商业使用；署名显示「中央通訊社」，保留标题及原文链接，不引用全文或图片。
- RTHK：采用[中文](https://news.rthk.hk/rthk/ch/rss.feed)与[英文](https://news.rthk.hk/rthk/en/rss.htm)官方目录提供的频道。目录旧域名会跳至 HTTP；直接使用其指向的 `rthk9.rthk.hk` HTTPS 地址并重新检查 robots，不跟随不安全降级。
- 日本：朝日新聞[官方 RSS 目录](https://www.asahi.com/information/service/rss.html)、毎日新聞[RSS](https://mainichi.jp/rss/)、nippon.com[官方目录](https://www.nippon.com/ja/rss_list/)，以及 Impress、JETRO、日本銀行、財務省官网直接提供的 RSS。仅标题导航，保留原文语言、来源和链接；RSS 内的说明、摘要、文章及图片不保留。
- 其他新增频道来自对应媒体自己域名的公开 RSS，或其官网明确提供的分发域名。连通成功仅证明技术可用；不宣称获得商业转载许可，不转售、不投放广告、不存全文。使用条件变化时停用，不购买许可。
- ITmedia：其[RSS 条件](https://corp.itmedia.co.jp/media/rss_condition/)对删改、仅摘录展示及应用集成有限制，本次不启用，不能因有 RSS 就推定适合公开聚合。
- NNA：按用户要求排除，不提供任何入口或新闻，不使用私有数据或会员采集逻辑。原 NNA 项目保持不变。

候选来源出现 401/403、robots 禁止、验证码、格式错误、过期或时间不明时保留失败说明，不能改用登录会话、第三方代理或私有 API 绕过。本次 PR 没有变更原 NNA 项目或其正式运行时间。

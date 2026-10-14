# 来源与第三方数据

本项目用途为个人、非商业 RSS 阅读与原文导航。发布者保留内容版权；来源连通测试不能证明公开再分发获得授权。网站展示署名与原文链接，没有全文、摘要、图片、广告或付费功能。

- BBC News：[RSS 说明](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm)。BBC 的 RSS/元数据条款要求署名与附近链接，并对更改 feed、品牌以及商业使用作限制；上线前应检查当前 [BBC 使用条款](https://www.bbc.co.uk/usingthebbc/terms/)，不要将本项目视为已取得商业元数据许可。
- The Guardian：[RSS 使用说明](https://www.theguardian.com/help/feeds)、[公开许可条件](https://www.theguardian.com/info/2022/nov/01/open-licence-terms)。本项目限制为个人非商业用途，并为每条标题提供来源与原文链接。
- Al Jazeera：[官网](https://www.aljazeera.com/)、[条款](https://www.aljazeera.com/terms-and-conditions)。公开 RSS 为读取入口，不自动赋予其他用途的许可。
- DW：[官网](https://www.dw.com/)。使用其公开 RSS，不绕过访问限制；公开发布前复核其版权和当前使用条件。
- CNA：[条款](https://www.channelnewsasia.com/terms-of-use)。仅公开 RSS 元数据；不抓取正文或媒体。公开聚合的具体权利仍需复核。
- NASA：[媒体使用指引](https://www.nasa.gov/nasa-brand-center/images-and-media/)。本项目仅使用公开资讯标题和原文链接，不使用徽章、人物图片、第三方媒体或暗示 NASA 背书。
- Euronews：[官网](https://www.euronews.com/)。仅公开 RSS 标题与原文导航；公开发布前复核当前条款。

若发布者不允许所需公开使用，应移除该订阅并替换免费允许的公开来源；不购买许可或绕过技术限制。robots.txt 是访问规则检查，不是内容版权授权。当前尚未公开部署，因此条款复核可在上线确认时完成。

## 海岸线

`site/assets/land.json` 来自 Natural Earth 的 `ne_110m_land`，保留每个多边形外环并将经纬度四舍五入至三位小数，无国界。

- [数据来源](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson)
- [Natural Earth 公共领域使用条款](https://www.naturalearthdata.com/about/terms-of-use/)

数据随项目保存，浏览器不连接地图服务，无 API Key，无地图计费。文件约 85 KB；无需持续下载更新。

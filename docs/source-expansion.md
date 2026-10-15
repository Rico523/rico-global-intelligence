# 三语言新闻源扩充（用户批准合并发布）

保留现有 12 个英文 Feed、现有网站布局和每日 UTC `17 0,12 * * *` 的正式运行时间。配置扩至 86 个 Feed / 28 个媒体或机构（英文 37、中文 27、日语 22）。频道数按 Feed ID 统计；媒体按 `media` 去重归并，不能把多个频道说成多个媒体。

新增语言、媒体来源与既有国家、主题、关键词组合筛选；保留三种语言原文。补充中日文保守分类/地理规则，未知地点不编造坐标。数据 schema 拒绝正文和会员摘录字段，NNA 域名不能加入公开采集配置。

## 真实验证

2026-10-16（日本时间）最终验证：

| 环境 | 有效媒体/机构 | 有效 Feed | 中文/日语/英文 Feed | 采集条目 | 保留条目 | 耗时 |
|---|---:|---:|---|---:|---:|---|
| GitHub Ubuntu | 28/28 | 86/86 | 27 / 22 / 37 | 2,556 | 600 | 45.36 秒 |
| 本地 Mac | 28/28 | 86/86 | 27 / 22 / 37 | 2,576 | 600 | 150 秒硬时限内完成 |

云端保留新闻：中文 304、日语 122、英文 174；本地保留新闻：中文 302、日语 119、英文 179。采集条目为去重前的 Feed 条目，600 为去重、14 天保留及数量上限后的新闻，并不代表所有频道的全部历史。两处请求时点不同，因此条目数略有差别。最终启用配置的本地及云端实测失败来源均为 0。

- [最终逐源本地报告](audits/local-2026-10-16.json)：86 个来源的 HTTP、格式、编码、可解析条目数、失效/过期计数、发布日期范围、来源数量和耗时；没有文章正文。
- [最终云端汇总](audits/cloud-2026-10-16.json)及[成功运行日志](https://github.com/Rico523/rico-global-intelligence/actions/runs/38817374865)：34 项测试与真实来源检查通过，权限只有 contents:read，没有部署步骤。
- [89 候选本地报告](audits/candidate-local-89-2026-10-16.json)保留筛选过程证据；不等于最终启用配置。首轮云端 86/89，CNA Singapore 被 robots 禁止，Khmer Times 两个频道 robots 403；3 个新增 Feed 随后移除，不重试绕过。
- 新闻 JSON 本地约 305 KB；含两份历史的 site 约 1.01 MB，低于 4 MB 发布上限。新增来源没有提高新闻保留量。

34 个离线测试通过，包括旧编码 GB18030/Big5/Shift-JIS、UTF-16 DTD 拒绝、时区、跨国地理、中文印度/印尼碰撞、单站串行与 robots 缓存、请求预算、gzip 解压上限、禁止正文公开、确认网页不含 NNA 和只读 PR 工作流。Node 语法检查和 actionlint 通过。

浏览器用真实采集的 JSON 验证中文、日语、英文各自筛选、标题/来源/日期/原文链接显示。实际测得浏览器内宽 390、高度 844：单列布局、筛选两列、无横向溢出，中日英筛选与地球按钮正常；不是实体 iPhone Safari 测试。

## NNA 排除范围

2026-10-16 用户明确要求「NNA 不要，其他可接入的，合并发布」。已移除 NNA 的 11 市场目录文件、界面、脚本和样式，并增加网页不得包含 NNA 的回归检查。NNA 不计入 86 个有效 Feed；采集器继续拒绝该域名。原 NNA 项目未修改。

ITmedia 因 RSS 摘录条件不适合当前展示方式，也不启用，详见 SOURCE_POLICY.md。

## 失败候选与不启用原因

- CNA Singapore：云端 robots 禁止；Khmer Times 两个频道：云端 robots 403，均从最终启用配置移除。
- NHK 旧域名返回过期 RSS；新域名实测 401，不尝试认证。
- 联合新闻网 RSS 返回过期条目；Global Voices 中文没有 14 天内有效条目。
- 财新和 RTHK 旧目录地址发生 HTTP 降级。财新未启用；RTHK 使用官网旧地址所指向、并重新验证成功的 HTTPS 域名。
- 中时 403；TechNode 中文、The Irrawaddy 部分地址 403 或格式不合法；不尝试代理、登录或绕过访问限制。
- 36氪、Diamond 和多个错误频道返回 HTML / DTD，不能作为 RSS 解析。
- 明報、ADB、East Asia Forum、TechNode、METI、Hong Kong Free Press 等 robots 获取失败，不沿用猜测许可。
- 其他 404 候选（包括旧 NHK 目录以外的错误频道、HK01、香港政府部分旧路径、The Star、PNA、澎湃等）不进入配置；没有为了数量保留无效源。

## 请求、费用和数据增长

12 个工作线程，同站点串行，最少 0.5 秒间隔并遵守更长 robots crawl-delay/request-rate；每站点每次运行一次 robots（含失败缓存），每 Feed 一次请求，每请求最多两次 HTTPS 重定向，不重试。软调度预算 125 秒，硬时限仍 150 秒；正式发布 job 4 分钟、维护 job 1 分钟不变。JSON 仍最多 600 条/14 天/1 MB，历史最多 2 份、整个 site 最多 4 MB，不把周期新闻数据提交 Git。

按 86 Feed 最坏每次 172 个逻辑请求、每日 344 个请求估算，实际同站点共享 robots 更少。正式运行每月最多约 300 分钟的 job 上限；公开仓库标准 GitHub Runner 计算时间免费。PR 检查独立只读、最多 5 分钟，不上传 artifact、不存 cache。原 Pages 产物仍保留 1 天，约 8 MB 上限估算；账户共享 500 MB 存储边界与既有 0 预算保护仍须保持。不会自动升级到收费方案，不改账户预算或他项目设置。

2026-10-16 核对 [GitHub Actions 官方计费](https://docs.github.com/en/billing/concepts/product-billing/github-actions)：公开标准 Runner 免费，大型 Runner 不免费，artifact 存储仍有账户共享额度。本 PR 使用既有标准 `ubuntu-24.04`；没有新增付费服务、API、AI、数据库或服务器。

robots 解析遵循 [RFC 9309 2.3.1.5](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.3.1.5)，使用可解析的 REP 规则并忽略其他行。部分官方 RSS 分发域名的 robots 以 200 返回普通 HTML 落地页（没有 REP 指令），报告以 robots_format=html 如实标记；这不等于取得内容转载许可。验证码或访问挑战、403、网络错误继续跳过，不运行网页脚本或认证流程。

## 最终来源构成

| 媒体 / 机构 | Feed 数 | 语言 |
|---|---:|---|
| ANTARA | 2 | English |
| ASEAN | 1 | English |
| Al Jazeera | 1 | English |
| BBC | 6 | English / 日本語 / 中文 |
| Bangkok Post | 2 | English |
| DW | 2 | English / 中文 |
| Euronews | 1 | English |
| Global Voices | 1 | 日本語 |
| Impress | 4 | 日本語 |
| JETRO | 1 | 日本語 |
| Malay Mail | 2 | English |
| RFI | 2 | 中文 |
| RTHK | 8 | English / 中文 |
| SCMP | 4 | English |
| The Diplomat | 1 | English |
| The Guardian | 5 | English |
| The Laotian Times | 2 | English |
| VnExpress | 3 | English |
| nippon.com | 6 | English / 日本語 / 中文 |
| 中央通訊社 | 9 | 中文 |
| 日本銀行 | 2 | English / 日本語 |
| 朝日新聞 | 9 | 日本語 |
| 東洋経済 | 1 | 日本語 |
| 毎日新聞 | 1 | 日本語 |
| 科技新報 | 3 | 中文 |
| 自由時報 | 5 | 中文 |
| 財務省 | 1 | 日本語 |
| 香港政府 | 1 | English |

发布授权：用户已批准排除 NNA 后合并 PR #1 并正式发布。正式 pages.yml 与定时频率保持不变，原 NNA 项目不修改。

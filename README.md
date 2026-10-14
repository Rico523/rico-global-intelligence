# Rico Global Intelligence

免费的个人全球新闻情报中心：Python 标准库采集 RSS/Atom，原生 HTML/CSS/JavaScript 与 Canvas 展示，GitHub Actions 定时采集，GitHub Pages 静态托管。没有 AI 分析、API Key、云数据库、付费地图、外部字体或运行时第三方包。

**公开源码仓库已创建：https://github.com/Rico523/rico-global-intelligence 。GitHub Pages 已发布，费用门禁已核实；每天两次自动更新已启用。网站：https://rico523.github.io/rico-global-intelligence/ 。**

## 本地运行

在本项目目录执行（Mac 与 GitHub Ubuntu，Python 3.11+）：

```sh
python3 -m unittest discover -s tests -v
python3 collector/collect.py
python3 collector/validate.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory site
```

浏览器访问 `http://127.0.0.1:8765/`，不要直接双击 HTML。停止预览用 Ctrl-C。

Mac 的 Python.org 安装若缺少 CA 证书，采集器会额外加载 `/etc/ssl/cert.pem`；始终校验 HTTPS 证书，不使用忽略 TLS 的选项。不要运行其他项目的脚本或修改其配置。

## 功能与结构

- 标题、原文链接、来源、真实发布时间；支持 RSS 2、RDF RSS 和 Atom。
- UTC 存储；按浏览器时区显示。无时区或无发布时间的条目不进入新闻列表。超过 14 天及明显未来时间的新闻被跳过。
- 原文 URL 去除常见跟踪参数，并按 URL 或规范化标题去重。不同媒体的相似报道仍可能分别出现。
- 七个类别：全球、政治、经济金融、科技/AI、亚洲、能源、贸易供应链。AI 是新闻主题，不运行 AI 模型。
- 标题中的明确国家名/民族形容词用于国家标签；不凭媒体总部或含糊城市名推断事件国家。位置不明及跨国新闻保留列表而不绘制坐标。
- 地球支持鼠标/触摸拖动、方向键旋转、按钮缩放和重置、点击国家参考标记筛选。标记不是事件精确经纬度。
- 搜索、类别和国家/地区组合筛选、分类统计、分批显示、原文链接、来源状态、最后尝试/成功时间和数据过期提示。
- 深色响应式网页；无自动持续动画。移动版标记显示新闻数量，点击后显示国家筛选。

```text
collector/collect.py       采集、规则、去重与有界历史
collector/restore.py       从上一版 Pages 恢复数据
collector/validate.py      发布前校验文件与数据
collector/maintenance.py   30 天无提交时的小型维护提交
config/sources.json        可配置 RSS 来源
site/                     Pages 发布目录
site/data/news.json        最新真实新闻及来源状态
site/data/history/         最多两份历史快照（不进入 Git）
site/assets/land.json      随项目保存的公共领域海岸线
.github/workflows/pages.yml  手动发布工作流，定时默认注释
tests/                   离线单元和集成测试
```

## 采集来源

第一版是 **12 个 RSS 订阅，来自 5 家发布机构**，不是 12 家独立媒体：

| 机构 | 订阅范围 |
|---|---|
| BBC News | World、Business、Technology、Asia（4 个） |
| The Guardian | World、Business、Technology、Energy、Asia Pacific（5 个） |
| Al Jazeera | 全站新闻 |
| DW | World |
| Euronews | News |

实际 URL 位于 `config/sources.json`。UN News 和 Nature 在候选实测中分别出现响应无法解析和没有近期有效条目，未列入正式配置。CNA 在云端实测中被 robots.txt 禁止，已替换为 Guardian Asia Pacific；NASA 在后续云端运行中返回 429 限流，已从启用列表移除。不会绕过这些限制。来源状态基于本次抓取结果，不保证永久可用。

仅保存标题与链接等元数据，不下载全文、图片或视频，不绕过登录、付费墙或访问限制。采集前检查 robots.txt；禁止访问、403、异常 robots 响应或超长等待要求时跳过来源。RSS 内容的版权仍归发布者，公开可访问不等于无条件转载许可。个人非商业使用，公开发布前按 `SOURCE_POLICY.md` 核对来源规则；不自动申请收费许可。

新增来源只需配置唯一 id、name、HTTPS url、默认 category。配置可容纳最多 120 个来源；本阶段只启用 12 个。扩展到 100 个以上需要重新验证网络预算和站点规则，程序不会自动提高频率、时间或费用预算。

## 免费额度与安全保护

- 仅公开仓库、标准 `ubuntu-24.04`。工作流在私有仓库或未设置 `ZERO_COST_CONFIRMED=true` 时跳过。
- 支持手动触发和已启用的每天两次 schedule；没有 push 或 PR 触发。
- 每天两次：UTC 00:17 / 12:17，即日本时间 09:17 / 21:17；定时可能延迟，不是实时推送。
- 工作流统一 concurrency，最多一个运行中的实例。发布 job 超时 4 分钟，维护 job 超时 1 分钟，顺序执行；排队时间不属于运行时间。
- 采集进程硬时限 150 秒，最多 4 个请求工作线程。连接/读操作超时 10 秒，流式大小检查。每来源最多两次逻辑请求（robots + RSS），每请求最多两次 HTTPS 重定向；没有应用层重试。恢复上一版最多 3 次逻辑请求，维护 API 最多 3 次。
- RSS 响应最多 2 MB，每个来源检查前 100 个条目；最新最多 600 条、14 天。每个新闻 JSON 最多 1 MB，历史最多 2 份，整个发布目录最多 4 MB。
- 正常来源故障不影响其他来源；全部失败仍写失败状态并保留有效旧新闻。发布后任务标红方便发现故障。若进程被硬时限终止，保留原子写入的数据，网页通过最后成功时间提示过期。
- 本地文件锁拒绝重复采集。数据更新使用同目录临时文件原子替换。
- 新闻数据不由 Actions 提交到 Git；从上一版 Pages 下载有界新闻和历史。首次发布使用随代码提供的真实种子数据。
- Pages 产物保留 1 天，不创建 Actions cache，不使用 Packages、LFS、自托管/大型 Runner 或付费域名。
- 官方 Actions 固定完整 SHA；checkout 不保留凭证。发布 job 只有读代码、写 Pages 和 OIDC 权限；维护 job 单独拥有本仓库 contents:write，Token 仅传请求头，不写入文件。
- 公开仓库连续 60 天没有活动，定时工作流可能被停用。维护脚本仅在最近提交超过 30 天时写一个不到 100 字节的状态文件，约每月一次；不提交新闻。分支保护若禁止 Token 提交，维护 job 会失败，需人工维护活动或之后改用其他免费调度。

GitHub 官方规则确认公开仓库的标准托管 Runner 运行时间免费，GitHub Free 支持公开仓库 Pages。**这不代表 Actions 存储没有计费边界。**Artifacts 与 Packages 的免费存储额度由账户共享（GitHub Free 为 500 MB），需检查其他仓库已有用量。按本项目 4 MB 发布上限、每日两次、产物保留 1 天估算，短期产物约 8 MB，仍不能代替账户检查。

已在账户页面确认 GitHub Free、现有 Actions 付费预算为 0 且付费使用被阻止，并原样保留现有设置。公开标准 Runner 的首次真实部署已经成功。以后更改计费设置前应重新检查；仅通知不是硬限制。如果当前账户不支持确认这一设置，保持门禁关闭，不启用发布。不要为了本项目更改账户全局预算、删除他项目产物或影响 NNA Morning Intelligence。

官方依据：
- [Actions 计费](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Pages 限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [预算设置及仓库范围](https://docs.github.com/en/billing/how-tos/set-up-budgets)
- [60 天无活动停用规则](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)

## 当前部署与维护

1. 创建新的公开 `rico-global-intelligence` 仓库，上传本项目目录内容至默认分支（工作流目录必须位于仓库根目录）。不要使用现有 NNA 仓库。
2. 检查费用保护、账户共享存储以及各来源非商业 RSS 使用条件。保持大型 Runner 和付费功能关闭。
3. 在新仓库 Settings → Pages 中选择 GitHub Actions。确认 Environment `github-pages` 允许默认分支部署；如有人工审核规则，需要相应批准。
4. 在 Settings → Secrets and variables → Actions → Variables 创建 `ZERO_COST_CONFIRMED`，值为 `true`。这是已完成账户检查的人工确认，代码本身不能读取或保证账户账单设置。
5. Actions 中手动运行 **Collect and deploy Rico**。确认 12 个来源状态、部署成功和费用为 0；网站地址由部署步骤输出，通常为 `https://<用户名>.github.io/rico-global-intelligence/`。
6. 默认分支已启用每天两次定时；如需暂停，只注释 `schedule` 与 `cron` 两行或禁用工作流。不要提高频率或放开费用门禁。

没有自定义域名依赖。`restore.py` 使用默认 github.io 地址；若以后使用自定义域名，需同步调整恢复路径并重新测试。未来如官方政策变化，先暂停该工作流，再研究替代方案，不能自动升级或付费。

## 验证范围与限制

测试覆盖 RSS/Atom、时区、异常日期、恶意 URL、实体 XML、去重、分类/位置、故障隔离、历史上限、数据大小、全失败保留、并发锁、维护提交和工作流保护。工作流经 YAML 解析和 actionlint 校验；首次真实 GitHub-hosted 运行与 Pages 发布已经成功；上线验收结果见 ACCEPTANCE.md。

网页已在浏览器验证桌面及 iPhone 宽度布局、搜索、组合筛选、地球拖动与标记点击；不是实体 iPhone Safari 测试。规则分类不是语义理解，国家识别以保守为原则，会漏标。下一阶段优先根据使用反馈修正规则和改善来源稳定性，不加入 AI 或扩大到 100 源。

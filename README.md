# Rico Global Intelligence

免费的个人全球新闻情报中心：Python 标准库采集 RSS/Atom，原生 HTML/CSS/JavaScript 与 Canvas 展示，GitHub Actions 定时采集，GitHub Pages 静态托管。没有 AI 分析、API Key、云数据库、付费地图、外部字体或运行时第三方包。

本次扩源状态：**PR 待审，扩源版未部署；下述上线状态指已有第一版。**

**公开源码仓库已创建：https://github.com/Rico523/rico-global-intelligence 。GitHub Pages 已发布，费用门禁已核实；每天两次自动更新已启用，且真实 schedule 运行已验证成功。网站：https://rico523.github.io/rico-global-intelligence/ 。**

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
- 原始语言 All / 中文 / 日本語 / English、媒体来源、搜索、类别和国家/地区组合筛选、分类统计、分批显示、原文链接、来源状态、最后尝试/成功时间和数据过期提示。
- 深色响应式网页；无自动持续动画。移动版标记显示新闻数量，点击后显示国家筛选。

```text
collector/collect.py       采集、规则、去重与有界历史
collector/restore.py       从上一版 Pages 恢复数据
collector/validate.py      发布前校验文件与数据
collector/maintenance.py   30 天无提交时的小型维护提交
collector/check_sources.py 独立实测 HTTP / XML / 编码 / 日期与计数，不保存文章
config/sources.json        可配置 RSS 来源
site/                     Pages 发布目录
site/data/news.json        最新真实新闻及来源状态
site/data/history/         最多两份历史快照（不进入 Git）
site/assets/land.json      随项目保存的公共领域海岸线
.github/workflows/pages.yml  既有定时发布工作流（本次不改变）
.github/workflows/source-check.yml PR 只读来源检查，不部署
tests/                   离线单元和集成测试
```

## 采集来源

本次分支扩充为 **86 个 Feed / 28 个媒体或机构**，包括英文 37、中文 27、日语 22 个 Feed。媒体数量按 `media` 字段归并，同一媒体的多个频道不重复计作媒体。原有 12 个英文 Feed 的 ID、URL 全部保留。实际有效数量以本次运行来源状态为准，不保证来源永久可用。

本次改动仍在 PR 分支，未经批准不合并，不改变线上网站。

新增来源包括中央通訊社、RTHK、自由時報、科技新報、RFI、nippon.com、朝日新聞、毎日新聞、Impress、JETRO、日本銀行、財務省，以及东南亚区域媒体。完整配置位于 `config/sources.json`；实测报告及失败候选见 [扩源验收记录](docs/source-expansion.md)。默认保留原始语言，不翻译、不调用 AI。

NNA 11 个市场仅提供官网入口，**不计入 86 个有效 Feed**。只读检查过原项目的公开国家路由发现和日期验证规则，没有修改原项目，也没有复制私有数据、凭证或会员采集模块。现有私有使用授权不等于公开转载许可；在确认公开标题许可之前，本采集器拒绝 NNA 域名进入公开新闻流。详见 [来源政策](SOURCE_POLICY.md)。

仅保存标题、署名、日期、链接及规则标签，不下载文章正文、图片或视频，不绕过登录、付费墙、验证码或访问限制。采集前检查 robots.txt；禁止访问、403、异常响应或超长等待要求时跳过。公开 RSS 不等于无限再分发许可，个人非商业展示仍须遵守各媒体条件。

新增来源配置 `id`、`name`、`media`、`language`（zh/ja/en）、HTTPS `url`、默认 `category`。最多 120 个 Feed，不自动提高频率、运行时限或费用预算。独立实时检查：

```sh
python3 collector/check_sources.py --report /tmp/rico-source-check.json
```

报告只含 HTTP、RSS 格式、编码、条目数、日期范围、失败原因及语言/媒体统计，不保存原始 feed 或文章。少于 80 个有效 Feed、或缺失一种语言时检查失败。网站仍显示全部来源的成功/失败状态。

## 免费额度与安全保护

- 仅公开仓库、标准 `ubuntu-24.04`。工作流在私有仓库或未设置 `ZERO_COST_CONFIRMED=true` 时跳过。
- 支持手动触发和已启用的每天两次 schedule；发布工作流没有 push 或 PR 触发。独立 PR 检查工作流只有 contents:read，超时 5 分钟，不部署、不提交、不上传 artifact。
- 每天两次：UTC 00:17 / 12:17，即日本时间 09:17 / 21:17；定时可能延迟，不是实时推送。
- 工作流统一 concurrency，最多一个运行中的实例。发布 job 超时 4 分钟，维护 job 超时 1 分钟，顺序执行；排队时间不属于运行时间。
- 采集进程硬时限 150 秒，最多 12 个工作线程；同站点请求串行，最小间隔 0.5 秒并遵守更长 crawl-delay / request-rate。调度软预算 125 秒，预留请求结束与保存时间。连接/读操作超时 10 秒，流式大小检查。每站点每次运行最多一次 robots 请求（含失败缓存），每 Feed 最多一次 RSS 请求，每请求最多两次 HTTPS 重定向；没有应用层重试。恢复上一版最多 3 次逻辑请求，维护 API 最多 3 次。
- RSS 响应最多 2 MB，每个来源检查前 100 个条目；最新最多 600 条、14 天。每个新闻 JSON 最多 1 MB，历史最多 2 份，整个发布目录最多 4 MB。
- 正常来源故障不影响其他来源；全部失败仍写失败状态并保留有效旧新闻。发布后任务标红方便发现故障。若进程被硬时限终止，保留原子写入的数据，网页通过最后成功时间提示过期。
- 本地文件锁拒绝重复采集。数据更新使用同目录临时文件原子替换。
- 新闻数据不由 Actions 提交到 Git；从上一版 Pages 下载有界新闻和历史。首次发布使用随代码提供的真实种子数据。
- Pages 产物保留 1 天，不创建 Actions cache，不使用 Packages、LFS、自托管/大型 Runner 或付费域名。
- 官方 Actions 固定完整 SHA；checkout 不保留凭证。发布 job 只有读代码、写 Pages 和 OIDC 权限；维护 job 单独拥有本仓库 contents:write，Token 仅传请求头，不写入文件。
- 公开仓库连续 60 天没有活动，定时工作流可能被停用。维护脚本仅在最近提交超过 30 天时写一个不到 100 字节的状态文件，约每月一次；不提交新闻。分支保护若禁止 Token 提交，维护 job 会失败，需人工维护活动或之后改用其他免费调度。

GitHub 官方规则确认公开仓库的标准托管 Runner 运行时间免费，GitHub Free 支持公开仓库 Pages。**这不代表 Actions 存储没有计费边界。**Artifacts 与 Packages 的免费存储额度由账户共享（GitHub Free 为 500 MB），需检查其他仓库已有用量。按本项目 4 MB 发布上限、每日两次、产物保留 1 天估算，短期产物约 8 MB，仍不能代替账户检查。86 Feed 每次最多 86 个 Feed 请求和不超过 86 个 robots 请求；每日不超过 344 个逻辑来源请求（通常少于此数），无重试。按满额每次 5 分钟、每日两次估算每月 300 分钟；公开标准 Runner 计算时间免费。新闻大小和历史上限没有随扩源增加，正常运行不增加 Git 新闻提交。

已在账户页面确认 GitHub Free、现有 Actions 付费预算为 0 且付费使用被阻止，并原样保留现有设置。公开标准 Runner 的首次真实部署已经成功。以后更改计费设置前应重新检查；仅通知不是硬限制。如果当前账户不支持确认这一设置，保持门禁关闭，不启用发布。不要为了本项目更改账户全局预算、删除他项目产物或影响 NNA Morning Intelligence。

官方依据：
- [Actions 计费](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Pages 限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [预算设置及仓库范围](https://docs.github.com/en/billing/how-tos/set-up-budgets)
- [60 天无活动停用规则](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)

## 当前部署与维护

1. 本项目已有公开仓库。扩源通过独立 PR 审阅，批准后才合并；不要创建重复仓库或改动 NNA 项目。
2. 检查费用保护、账户共享存储以及各来源非商业 RSS 使用条件。保持大型 Runner 和付费功能关闭。
3. 在新仓库 Settings → Pages 中选择 GitHub Actions。确认 Environment `github-pages` 允许默认分支部署；如有人工审核规则，需要相应批准。
4. 在 Settings → Secrets and variables → Actions → Variables 创建 `ZERO_COST_CONFIRMED`，值为 `true`。这是已完成账户检查的人工确认，代码本身不能读取或保证账户账单设置。
5. Actions 中手动运行 **Collect and deploy Rico**。确认当前配置的来源状态、部署成功和费用为 0；网站地址由部署步骤输出，通常为 `https://<用户名>.github.io/rico-global-intelligence/`。
6. 默认分支已启用每天两次定时；如需暂停，只注释 `schedule` 与 `cron` 两行或禁用工作流。不要提高频率或放开费用门禁。

没有自定义域名依赖。`restore.py` 使用默认 github.io 地址；若以后使用自定义域名，需同步调整恢复路径并重新测试。未来如官方政策变化，先暂停该工作流，再研究替代方案，不能自动升级或付费。

## 验证范围与限制

测试覆盖 RSS/Atom、时区、异常日期、恶意 URL、实体 XML、去重、分类/位置、故障隔离、历史上限、数据大小、全失败保留、并发锁、维护提交和工作流保护。工作流经 YAML 解析和 actionlint 校验；真实 GitHub-hosted 手动及 schedule 运行与 Pages 发布均已成功；第一版历史验收见 ACCEPTANCE.md；本次分支的真实来源、语言及新闻数量见 docs/source-expansion.md，不能把历史部署验收当作扩源已经上线。

网页已在浏览器验证桌面及 iPhone 宽度布局、搜索、组合筛选、地球拖动与标记点击；不是实体 iPhone Safari 测试。规则分类不是语义理解，国家识别以保守为原则，会漏标。下一阶段优先根据使用反馈修正规则和改善来源稳定性，不加入 AI。扩源通过 PR 审阅后才进入正式采集，不自动合并或发布。

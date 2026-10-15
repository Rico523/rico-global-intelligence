# Rico Global Intelligence — Phase 1 上线验收

正式网站：<https://rico523.github.io/rico-global-intelligence/>  
源码仓库：<https://github.com/Rico523/rico-global-intelligence>  
已部署代码：`1ad7938b623380bc9b06a651aa3788b9a3ad65cd`  
已验证的真实定时运行：<https://github.com/Rico523/rico-global-intelligence/actions/runs/38683608402>

## 完成状态

网站已可通过 HTTPS 正常使用，且 **GitHub 定时事件已经实际自动运行成功**，不依赖本地电脑保持开机。原生 Canvas 地球支持鼠标/触摸拖动、键盘旋转、缩放、重置和国家标记筛选；新闻支持搜索、类别与国家/地区组合筛选、分页、统计、来源及原文链接、健康状态和最后更新时间。位置不明确或跨国新闻不绘制坐标；标记是国家参考点，不是事件精确位置。

后端使用 Python 标准库，支持 RSS/Atom、UTC 日期、去重、规则分类/标签、失败隔离和有限历史。没有 AI 分析、付费 API、云数据库、付费地图或其他付费依赖。

## 真实新闻与来源

最近已验证成功采集：**2026-10-15 13:51:02 JST**。当前 **600 条**去重真实新闻；**12/12 RSS 来源可用**，来自 5 家发布机构。本次解析 310 条近期有效条目，与有界历史合并。没有模拟新闻。

| 来源 | 本次有效条目 | 状态 |
|---|---:|---|
| BBC World | 29 | 可用 |
| BBC Business | 28 | 可用 |
| BBC Technology | 17 | 可用 |
| BBC Asia | 17 | 可用 |
| The Guardian World | 45 | 可用 |
| The Guardian Business | 16 | 可用 |
| The Guardian Technology | 31 | 可用 |
| The Guardian Energy | 20 | 可用 |
| Al Jazeera | 25 | 可用 |
| DW World | 12 | 可用 |
| The Guardian Asia Pacific | 20 | 可用 |
| Euronews | 50 | 可用 |

CNA 因云端 robots.txt 禁止访问，替换为 Guardian Asia Pacific；NASA 因云端返回 429 限流而移出启用列表。未绕过限制或无限重试。

## 云端与费用保护

- 工作流为 active，默认分支启用 `17 0,12 * * *`，计划日本时间每天 09:17 / 21:17。GitHub 免费调度可能明显延迟；此次已验证的 schedule 事件实际于日本时间 13:50 启动，并非准点执行。不承诺实时或准点推送。
- 真实定时运行状态 success，最新发布和来源检查均成功；三次开发验收手动运行也成功，分别 42、37、31 秒。
- 仅公开仓库、标准 Ubuntu 24.04 Runner；直接使用的官方 Actions 均固定完整 SHA，使用 Node 24 版本，消除旧运行时和 ubuntu-latest 迁移提示。
- concurrency 最多一个运行中实例；发布 job 4 分钟、维护 job 1 分钟顺序执行，采集进程 150 秒硬时限。网络请求数量、重定向、超时和响应大小均有界，无应用层重试。
- 最新最多 600 条 / 14 天、每个 JSON 最多 1 MB、两份历史、发布目录最多 4 MB。Pages 产物保留 1 天，不启用 Actions cache、Packages、LFS、大型 Runner 或付费域名。
- 最新两份历史已从正式网站实际下载并通过校验。旧快照会被后续定时更新清理；应读取最新 news.json 的 history_keys，不应使用旧索引检查已过期快照。
- 后续运行从上一版 Pages 恢复新闻与历史，不提交自动新闻至 Git；只有 30 天无提交时才可能写一次小型维护记录。已验证自动运行没有改动代码提交。
- 已只读核实 GitHub Free、原有 Actions 0 美元付费预算和付费用量阻止状态。未修改全局预算、付款信息、NNA 项目。仅设置本仓库费用确认变量。
- 按公开标准 Runner 和公开 Pages 免费条件运行，没有开通付费服务。账单记录存在显示延迟；未用“尚无记录”替代已结算账单验证。政策或账户设置变化时应重新检查，不得自动转为付费。

官方依据：[Actions 计费](https://docs.github.com/en/billing/concepts/product-billing/github-actions)、[Pages 限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)、[预算停止用量](https://docs.github.com/en/billing/how-tos/set-up-budgets)。

## 验证结果与范围

- **21 项 unittest 通过**；云端最终版本测试、采集、恢复、静态数据校验、上传与发布均成功。
- actionlint v1.7.12 检查通过；已实际验证手动和 schedule 两种触发。
- 线上新闻加载、Japan 搜索、能源 + Russia 筛选、国家标记点击和键盘旋转正常，未发现控制台错误。此前 575 条验收数据时，Japan 搜索 8 条、能源 + Russia 6 条、China 标记 8 条；条数随真实新闻更新变化。
- 本地 375 / 390 / 430 / 1440 像素响应式布局验证通过，无整页水平溢出；线上桌面布局已确认。上线验收时的视口覆盖未改变目标标签页尺寸，未将该尝试算作新增手机实测。没有实体 iPhone Safari 测试，线上沿用相同响应式 CSS。
- 下载包已同步当前线上新闻和两份历史，但不将本次生成数据提交回远程 Git 仓库。

## 后续建议

第一版已上线并可正常使用。优先观察来源稳定性、修正规则漏标，并补一次实体 iPhone Safari 检查；不加入 AI，不扩大到 100 源。来源可能限流或停用，系统保留有效旧数据并显示状态；免费 GitHub 调度不提供准点保障。

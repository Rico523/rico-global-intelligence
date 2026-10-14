# Phase 1 验收报告

最后实际采集：2026-10-14 07:15:49 JST。

## 完成功能

标准库 RSS/Atom 采集，HTTPS 校验、robots.txt 检查、失败隔离；URL/标题去重、UTC 时间处理、7 类分类、保守国家/地区标签；最多 600 条 / 14 天新闻、两份历史与原子保存。Canvas 地球、公共领域海岸线、国家参考标记、拖动/键盘旋转、缩放/重置、标记筛选、新闻列表、组合筛选、搜索、分类统计、原文链接、来源状态、成功时间和过期提示。没有 AI 模型或任何付费 API。

## 真实采集

13 个 RSS 订阅 / 7 家机构全部成功。本次解析出 341 条近期有效条目；与既有真实有限历史合并、去重后，当前保存 **552 条**。没有模拟新闻。最新 JSON 224584 字节；网站全部文件约 641.7 KB，包含 2 份历史。

| 来源 | 本次有效条目 | 结果 |
|---|---:|---|
| BBC World | 23 | 可用 |
| BBC Business | 34 | 可用 |
| BBC Technology | 17 | 可用 |
| BBC Asia | 17 | 可用 |
| The Guardian World | 45 | 可用 |
| The Guardian Business | 40 | 可用 |
| The Guardian Technology | 27 | 可用 |
| The Guardian Energy | 20 | 可用 |
| Al Jazeera | 25 | 可用 |
| DW World | 13 | 可用 |
| CNA Asia | 20 | 可用 |
| NASA | 10 | 可用 |
| Euronews | 50 | 可用 |

## 测试结果

- Python unittest：**21/21 通过**，包括失败保留、历史和大小上限、并发锁、HTTPS 降级拒绝、URL/日期、规则与月度维护行为。
- 静态数据/文件上限校验通过。
- YAML 解析通过；官方来源下载并校验 checksum 的 actionlint **v1.7.12** 检查通过。没有在 GitHub 上执行工作流。
- 浏览器真实数据加载成功；Japan 搜索 4 条，能源筛选 41 条，能源 + Russia 筛选 6 条；更多新闻从 60 条增加到 120 条。
- 地球拖动前后画面改变；点击中国标记进入 China 筛选。支持键盘和按钮操作。
- 375、390、430、1440 像素宽度没有整页水平溢出。没有捕获到 console error/warn。仅是浏览器尺寸验证，未用实体 iPhone Safari 验收。

## 云端配置与费用

手动触发工作流已准备；每天两次计划为日本时间 09:17 / 21:17，schedule 当前保持注释。只允许公开仓库和标准 Ubuntu Runner，费用人工确认变量默认未设置。禁止并发，发布 job 4 分钟 + 维护 job 1 分钟；采集进程 150 秒硬限时。无无限重试、Actions cache、LFS、Packages、付费 Runner 或自动新闻提交。Pages 产物保留 1 天。30 天无提交时最多写一次不到 100 字节的维护记录，避免 60 天闲置风险。

GitHub 官方说明公开仓库标准 Runner 运行时间免费，GitHub Free 支持公开仓库 Pages；Artifacts 与 Packages 存储按账户共享。**未检查具体账户共享用量或付费预算，不能承诺该账户已经具备零收费保障。**上线前只为新仓库核对 0 付费预算及停止用量规则，不修改 NNA 或全局预算。

官方来源：[计费](https://docs.github.com/en/billing/concepts/product-billing/github-actions)、[Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)、[预算与停止使用](https://docs.github.com/en/billing/how-tos/set-up-budgets)、[闲置停用](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)。

## 尚未执行

已获授权创建公开源码仓库 Rico523/rico-global-intelligence 并上传代码。尚未启用定时任务、发布 Pages 网站、修改其他项目或账户设置。没有正式网站 URL；默认部署后格式为 `https://<用户名>.github.io/rico-global-intelligence/`。当前本地代码未初始化 Git，上传前可在这个独立目录初始化，不影响其他项目。

**技术上已具备部署准备条件**，实际云端 Runner/Pages 运行、具体账户零费用条件及公开再发布来源条件仍需上线前核对。步骤见 README 和 SOURCE_POLICY；没有购买许可或服务。

## 下一阶段

先确认新公开仓库、检查零费用设置并手动部署一次；成功后经确认启用每天两次定时。观察来源故障和分类/位置漏标，改善有限规则；不增加 AI，不扩大到 100 源。上线后补一次实体 iPhone Safari 测试。若官方免费政策或内容使用条件不能满足，暂停相关云端操作，不自动付费升级。

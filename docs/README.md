# StoryOS 文档入口

> 更新：2026-10-09。文件名或历史结论中的 FINAL / READY / PASSED 不等于当前代码和真实生产通过；历史方案仅是当时快照。

## 当前规范与入口

- [项目执行约束](../AGENTS.md)、[本机启动入口](../START_HERE.md)
- [图文制作规范](../standards/制作规范_正式版.md)：不引入视频合成，保护人工确定的发布图
- [数据库开发规范](standards/Story_OS_数据库开发规范_V1.0.md)
- [仓库与配置治理](architecture/仓库目录与配置治理.md)

## 仍在实施或等待真实验收的任务

- [模型底座双通道收敛](StoryOS_模型底座双通道收敛与生产闭环最终实施方案_20261009.md)：代码已部分进入主线，模型消费者统一和真实生产能力尚未全量验收；禁止 OpenCodex 代理作为正式模型通道
- [架构减法与生产闭环](StoryOS_架构减法与真实生产闭环整改实施计划_20261008.md)：历史实施日志 + 剩余整改门禁，不能直接据此放行
- [《五十亩山地之后》续产审计](StoryOS_五十亩山地之后_四槽位续产准入与Codex交接_20261009.md)：**历史只读快照**，Frame 06/24 UNKNOWN Attempt 等须核销，不等于正式出图授权
- [生产问题历史索引](../reports/Story_OS_稳定生产闭环_暴露问题清单_20260911.md)：旧问题当前是否关闭需按代码与权威状态复核

## 架构参考

- [数据持久化分层与 JSON 瘦身](architecture/Story_OS_数据持久化分层与JSON瘦身改造方案_V1.0.md)
- [Episode JSON 资产迁移审计](Story_OS_episodes_JSON资产迁移审计_20260917.md)
- [架构与成熟度历史评审](Story_OS_全系统架构与成熟度评审_20260916.md)

## 文档历史与清理记录

- [2026-10-09 文档清理执行记录](reports/StoryOS_文档清理实施记录_20261009.md)
- [治理历史](archive/governance-history/)、[各阶段历史](archive/phase-history/)、[历史问题](archive/issue-history/)
- [旧数据库设计](archive/database-legacy/)、[冻结的 Phase10](archive/phase10-frozen/)、[V2 演进](archive/v2-evolution/)
- 旧总迭代 V1.0/V1.1、多模式编排 V1.0/评审已退出当前执行入口；不要从归档资料发起新任务。
- 未跟踪的 Markdown 草案、SQLite 试验方案与剧集性能记录本轮不清理；处理前要先确认独有内容与真实状态。


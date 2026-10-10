# StoryOS Production Revision 受控迁移交接（2026-10-10）

> 本页是运营检查单，不是迁移批准、Visual Lock PASS 或付费生图授权。唯一目标 Episode：《五十亩山地之后》。

## 已验证

- 生产库通过项目 `.storyos/runtime-launcher/runtime.env` 连接，库名 `STORY_OS_RUNTIME`，MySQL 8.0.46，`lower_case_table_names=0`。
- `TB_GENERATION_ATTEMPT` 与 `TB_REVIEW_RECORD` 已存在；四张 `TB_PRODUCTION_REVISION*` 表尚不存在。
- `scripts/storyos_revision_migration_plan.py` 从 `platform/repository/mysql/schema_v2.py` 精确选择四个 CREATE TABLE，输出各 SQL SHA-256 与 `PLAN_READY_NOT_AUTHORIZED`；**只执行 SELECT，不执行 DDL**。
- 全新独立 TEST_ONLY MySQL 实际执行四表 DDL，通过迁移前计划与迁移后表/约束核验。发现并修正 MySQL 8 `CHECK_CLAUSE` 中反斜杠转义导致的误判。

## 正式执行前必须逐项确认

1. **备份与恢复验收**：从正式库生成受限权限的全量快照（含已有 Attempt、Review、Ledger 等历史表），保存到仓库外受保护目录；核对备份 SHA-256，并在独立测试库完成恢复演练。备份路径及验证记录不得包含明文密码。
2. **维护授权**：指定负责人批准维护时间，停掉可能写入相同正式 MySQL 的 Scheduler / Driver / Worker，核对本地其他 Episode 不受误伤。不得以关闭 OpenCodex 替代停写验证。
3. **当前结构一致性**：在写入前重新执行
   `python scripts/storyos_production_env.py scripts/storyos_revision_migration_plan.py`。
   只有确认为 `PLAN_READY_NOT_AUTHORIZED` 且四表全缺失时，才准备下一步。任何部分存在、错误库名、数据库连接失败均停下人工核查。
4. **受控迁移**：由被授权的正式迁移操作者在明确维护窗口执行 `schema_v2.DDL_STEPS` 中的四个 `create_production_revision*` 步骤，不运行 `apply_schema` 全库批量建表，不自动迁移别的 Episode，不修改旧 Attempt；若遇到部分失败，停止并保存执行回执，禁止盲目删除已建的表。
5. **迁移后检查**：执行
   `python scripts/storyos_production_env.py scripts/storyos_revision_schema_readonly.py`，
   必须输出 `READY_FOR_FURTHER_ADMISSION`；再运行计划工具预期为 `ALREADY_INSTALLED`。核对历史 Attempt/Review 行数与备份基线，并检查服务恢复条件。
6. **生产权限另行准入**：即使 Schema READY，也不得自动创建/激活 Revision、扩额、恢复旧 `OUTCOME_UNKNOWN` 或调用原生图片模型。需新 Revision 专属的四槽位 Visual Lock、Review、Fencing、预算和 Driver 授权。

## 故障处理

发生中断立即维持生产调度停写并记录最后成功的 DDL 步骤；不要直接 DROP 表或恢复覆盖旧 Attempt。由于 MySQL DDL 不属于通用事务整体回滚，先根据备份及现场状态评估恢复策略，必要时使用独立恢复库验证，再决定正式处理。

当前迁移状态：**等待备份恢复证明、维护批准和正式 DDL 执行**。

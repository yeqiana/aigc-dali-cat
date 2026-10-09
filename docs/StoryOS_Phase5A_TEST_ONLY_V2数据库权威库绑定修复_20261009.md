# StoryOS Phase5A TEST_ONLY MySQL V2 Authority Schema 对齐（2026-10-09）

## 已核实现场

- 正式 Windows StoryOSRuntime 运行于本地 MySQL 3307，默认库为 `STORY_OS_RUNTIME`；Worker 健康，OpenCodex 计划任务已禁用。
- 独立测试容器 `storyos-phase5a-mysql` 暴露 `127.0.0.1:3306`。这个 MySQL 8 实例区分数据库名大小写，`story_os_runtime` 与 `STORY_OS_RUNTIME` **是不同 Schema**。
- 容器两个 Schema 的 `TB_GENERATION_ATTEMPT`（大写表名）都存在。经只读 SQL 复核，小写 Schema 中该表有 **0 行**，大写 V2 Schema 中有 **10 行**，且均为历史 TEST_ONLY 外部单帧生成的 `SUCCEEDED` 记录。不能把它们当作本轮新 Canary 的成功凭据。针对全小写表名 `tb_generation_attempt` 的查找失败并不代表大写表名的表不存在。
- `generation_attempt_authority._connect()` 总是使用 `platform.repository.mysql.schema_v2.DATABASE_NAME`（值为 `STORY_OS_RUNTIME`），忽略 `STORYOS_MYSQL_DB` 默认值，以保持 V2 Authority 统一。
- 原 Canary `phase5a_collaborative_canary._preflight()` 和 `phase5a_initial_canary_input.prepare()` 都强制要求 `story_os_runtime` 小写默认库，导致准入检查与真正 Attempt Authority 使用的 Schema 不一致。

## 本次安全修复

- Canary 的正式准入和首次输入准备分别改成引用唯一的 V2 `DATABASE_NAME` 常量；必须同时满足 localhost / **3306** / **STORY_OS_RUNTIME**。
- 所有权限、全局 claim、最多 2 次真实生图、仅测试资产、正式审核及图像工具能力证据门禁保持原样；没有修改 `generation_attempt_authority` 的连接逻辑。
- 新增 7 条合同测试：禁止测试容器的小写 Schema、禁止正式 3307、禁止其他 Schema；只有 3306 的 V2 Schema 能通过数据库准入到达后续输入或 claim 检查。
- 本轮四槽位回归：10 + 12 + 15 + 11 = **48 passed**，`git diff --check` 通过。
- 未执行任何图片生成、正式图片 Attempt、预算重置或数据库写入；本补丁**不能**单独证明 `image_generation` 工具调用可用，也不能把既有 `OUTCOME_UNKNOWN` 改为成功。

## 生产边界

- 正式 Episode《五十亩山地之后》仍为 **2/25**；Frame 06、24 旧 Attempt 均为 `OUTCOME_UNKNOWN`，需按权威回执修复。
- 不得把 3306 测试库与 3307 正式数据库共用写连接，不得使用历史 TEST_ONLY 外部成功记录冒充本次 Phase5A Capability Canary。
- 主工作区 dirty 资产与生产素材保持不覆盖，补丁先在 `storyos-main-integration-20261009` 独立验证、提交，再以精确局部修改集成。
- 本系统只生产图文，不引入视频；图片只允许原生 Codex，不使用 OpenCodex 代理。

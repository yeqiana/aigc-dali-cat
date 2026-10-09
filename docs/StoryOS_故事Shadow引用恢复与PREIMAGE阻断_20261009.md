# StoryOS 故事 Shadow 审核引用恢复与 PREIMAGE 验收阻断（2026-10-09）

> 本记录仅含真实执行证据。Episode Stage、Story Review PASS、图片 Review Authority 和正式图片 Attempt 不允许根据文档或测试结果自动推进。

## 1. 真实根因：MySQL 大文档引用列表没有解包

- 正式《五十亩山地之后》原下一步为 `PRODUCT_REVIEW`，`review_kind=story-semantic-critic-shadow`，`executor=WORK`。
- `runtime_review_persistence.list_current()` 与 `list_attempts()` 直接将 MySQL 查询返回的 `RUNTIME_REVIEW_REQUEST_REF` 紧凑摘要交给上层，而 `load_path()` 原先已经支持外置引用文档的读回与 SHA-256 校验。这是两个读取入口的数据合同不一致。
- 生产审核引用的外置 JSON **实际存在、SHA-256 对得上**。真实创建时间 2026-10-02 23:14:02+08:00、审核期限 2026-10-02 23:29:02+08:00；旧列表投影只有 ID/status 等键而丢失时间戳，导致旧 Shadow 被误当作无期限的待审任务。
- 检查 7 个冻结源文件：6 个 SHA 与请求匹配、1 个已漂移。候选文件不存在，没有证据支持将其升级为 PASS。
- **真实生命周期操作已完成**：使用 `product_review_adapter.reconcile_request()` 对精确 ID `story-semantic-critic-shadow-a1-8a6b964754478812` 进行源漂移对账，生产回读确认 `AWAITING_PRODUCT_REVIEW -> SUPERSEDED`；没有产生候选、没有补审核模型、没有改 Episode 阶段/像素。
- 之后正式 `next_action` 从 `PRODUCT_REVIEW` 变为 `PREIMAGE_COMPILE`，细分 `PREIMAGE_VERIFY`，Stage 仍是 `STORYBOARD_LOCKED`。SUPERSEDED 是旧 Shadow 失效，不是 Story Review PASS。

## 2. 隔离集成工作树的代码修复

- 在 `runtime_review_persistence.py` 为两种列表读取新增共享 `_resolved_row_payload`：对引用读取外置文档，校验文件 SHA-256、review_kind、request_id、status 和 attempt；任何失配均明确失败，不伪造完整请求。
- `tests/system/test_runtime_review_persistence.py` 新增当前别名及 Attempt 文档恢复、SHA 不匹配、身份不匹配测试；定向组 21 passed + 3 subtests。
- `AGENTS.md` 与 `SKILL.md` 将旧“有 API Key 就优先走 OpenAI 图片 API”改成历史退役说明：当前图片生成只使用原生 Codex，OpenCodex、API 图片 Provider、Product Runtime 旁路均不得自行启用；新增文档合同回归。
- 这次改动只在 `storyos-main-integration-20261009`，不覆盖主工作树 133 条本地未提交改动。

## 3. 当前 PREIMAGE 的数据库阻断

- 正式环境使用的 MySQL 连接端口为 3307，与仅用于 Phase5A TEST_ONLY 的 Docker MySQL 3306 不同。
- `preproduction_handoff.verify()` 的实际查询及后续只读双路径测试均在 3307 连接返回 `OperationalError 1049: Unknown database 'STORY_OS_RUNTIME'`。对应 V2 schema 当前不可用，不能根据这里的失败推定 PREIMAGE 内容本身必定坏了。
- 禁止在没有现有数据库清单、Schema 来源与 Authority 对账之前自动 `CREATE DATABASE`、调整正式 runtime.env 或从 TEST_ONLY 数据库迁移。
- 正式下一步应先排除数据库 V2 Schema 连接/环境路由问题，随后再执行 PREIMAGE VERIFY；再决定是否需要派生重建，不得直接重新生图。

## 4. 只读 V2 Schema 准入证据与增量保护

- 正式 3307 连接的 `SHOW DATABASES` 返回 5 个 schema，其中相关仅有小写 `story_os_runtime`；**不存在区分大小写的 `STORY_OS_RUNTIME`**。小写旧库可读取到 28 张表，`TB_*`（V2）表计数 0。不能直接把 V2 Repository 的数据库参数从大写改为小写：表结构不兼容。
- 新增 `episodes/_system/preimage_storage_preflight.py`，使用 `information_schema` 做只读校验；检查精确 V2 Schema 身份及少量必需 V2 表，明确区分 `V2_SCHEMA_MISSING`、`V2_TABLES_MISSING`、`V2_SCHEMA_PRESENT_UNATTESTED`。**结构检查成功也永远不会发放生产写入权限**。
- 正式环境只读运行该模块输出：`status=V2_SCHEMA_MISSING`、`case_only_schema_present=true`、`schema_check_passed=false`、`production_authority_granted=false`。
- `tests/system/test_preimage_storage_preflight.py` 验证大小写别名不能放行、表不齐不能放行、元数据存在不产生 Authority、连接失败 fail-closed；4 passed。
- 生产阻断边界：在明确 V2 Schema 容器/迁移归属、对账计划和备份之前，不执行任何 `CREATE DATABASE`、DDL、数据库连接强制改写或 PREIMAGE 物化。

## 5. WORK PREIMAGE 执行门禁接入

- `runtime_dag.py` 的 WORK PREIMAGE 分支在 `PREIMAGE_FRAME_CONTRACT_COMPILE` 与 `PREIMAGE_VERIFY` 的第一个派生物化动作之前调用 `_assert_preimage_storage_schema()`。
- 只有配置 `episode_meta_store.mode=mysql/dual` 时才调用只读 V2 Schema Probe；`json` 模式不添加 MySQL 依赖。阻断码为 `PREIMAGE_V2_SCHEMA_BLOCKED:<probe status>`，只拒绝派生物化，不推进 Stage、不启动审核模型、不消耗图片 Attempt。
- 即使结构检查通过，也不代表 Review Authority 或生产写入批准；`production_authority_granted` 始终为 false。
- 新增 5 个 WORK PREIMAGE 门禁回归：MySQL/dual 缺库阻断、JSON-only 兼容、仅结构就绪不发放 Review Authority、两个 Host 分支均先校验再物化。
- 最新四槽位回归 A 51 passed + 6 subtests，B 21 passed + 3 subtests，C 39 passed，D 18 passed，共 **129 passed + 9 subtests**；未执行正式 PREIMAGE 物化。
- **权威核验限制**：之前对 Shadow 的 `SUPERSEDED` 持久化读回曾成功，但本轮 3307 的 V2 Schema 不可用，当前无法再次从同一运行时环境独立核验该记录。不得据此将 Story Review 标记 PASS；恢复 Schema/Authority 连接后应先重新对账。

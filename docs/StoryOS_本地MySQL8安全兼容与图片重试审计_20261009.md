# StoryOS 本地 MySQL 8.0 安全兼容复制与图片恢复阻断（2026-10-09）

> 范围：本轮真实执行证据。数据库复制、派生 Handoff 刷新与回归测试**不自动授予**生成、审核、发布或阶段迁移权威。

## 1. 数据库迁移实际验收

- 源：本机 Docker 容器 `mysql8.0`，映射 `127.0.0.1:3307`，MySQL 8.0.46，`lower_case_table_names=0`。
- 源数据库 `story_os_runtime` 有 28 张表，其中 27 张与 StoryOS V2 Schema 表一一对应（忽略大小写），另有 `platform_latest_record`。包含 Episode 18、Episode Contract 53、Runtime Review Request 113 条。
- 原迁移备份 `.storyos/runtime-launcher/backups/story_os_runtime-precutover-20261009.sql.gz` 已做 gzip 校验；原压缩包 SHA-256：`c66dd2dfc8e546b4215238b4abab2d75f5edcc0805cddea80d113a14d6269e5c`。
- V2 预期 27/27 张表均存在对应源表且字段集合相同；`TB_EVENT_LOG`、`TB_TRACE_SPAN`、`TB_ARTIFACT_INDEX` 字段顺序不同，使用显式列名映射，**没有采用危险的 `SELECT *` 复制**。
- 运行 `scripts/storyos_mysql_case_compat_copy.py plan` 回报 `PLAN_SAFE`，随后在源库完整保留的前提下新建独立 **`STORY_OS_RUNTIME`**。
- 复制结果 `COPY_VERIFIED`：**27 张表、4,380 行**，每表按主键排序计算 SHA-256，与源库复制前及复制后均一致；未更改 `runtime.env`、源 Schema 或图片 Attempt。
- 重新执行 `preimage_storage_preflight.inspect()` 返回 `V2_SCHEMA_PRESENT_UNATTESTED`、`schema_check_passed=true`。结构具备不等于生产写入许可，`production_authority_granted=false`。
- **后续使用约束**：这是一时点快照，源小写库与目标大写库不会自动双向同步。以后按 V2 Repository 写入的大写库应作为 V2 审查对象，不可假定两库持续一致；禁止重跑迁移脚本覆盖上面的数据。

## 2. 正式《五十亩山地之后》衔接

- 在目标 V2 Schema 中，精确确认过期 Story Semantic Shadow 的冻结源文件 7 项中 1 项漂移、候选不存在，依既有 `reconcile_request` 对账 `AWAITING_PRODUCT_REVIEW -> SUPERSEDED`，没有伪造 PASS。
- PREIMAGE: 人物、环境、Frame Contract、导演质量所有校验通过。Handoff 唯一旧错误为 `HANDOFF_SHA_MISMATCH:meta/resource-selection.json`。提前备份原 Handoff 与原 Resource Selection，在确定资源库绑定新旧选中 ID 相同且新快照为 fresh 后，只刷新派生 Handoff，**不改资源选择文件字节**。
- 更新后的 `preproduction_handoff.verify()` 和 `frame_contract.verify_all()` 均为无错误，Stage 仍 `STORYBOARD_LOCKED`；MySQL Generation Attempt 记录数前后均为 5，没有新图片生成。
- 之后正式 `next_action` 返回 `RETRY_TECHNICAL_FAILURES`，但 `image_scheduler plan` 返回 `ready=[]`。属于上层错误的重试乐观投影，不能直接作为模型派发许可。
- 真实 Frame06：`IMAGE_TOOL_NO_ARTIFACT`，原生图片 artifact 为 0；Frame24：`ASPECT_RATIO_MISMATCH`，历史 RAW 为 1448×1086、目标 1080×1350，不能无证据强行裁切/拉伸。
- V2 Generation Attempt 权威：Frame01 Attempt1/2、Frame05 Attempt1 为历史 `SUCCEEDED`；Frame06/24 Attempt1 均为 `OUTCOME_UNKNOWN`，Provider 字段记为历史 `opencodex`。历史数据不倒签成原生 Codex 生成，也不自行重置 Attempt。
- 在**安全集成分支**修改 Scheduler `_technical_retry_budget`：先确认上一次 Attempt 为可信 `FAILED_AFTER_DISPATCH` 才能自动重试；`OUTCOME_UNKNOWN`、成功回执冲突、失去回执全部 fail closed。上层 `next_action` 改为 `VERIFY_TECHNICAL_GENERATION_EVIDENCE`，阻断自动重复派发；直接调用重试入口也不能绕过。
- 原生 Codex-only 保持不变；直到图片工具真实能力、旧回执及新的合法 Attempt 通过审核，不执行新生图，不把实验 Canary 图算作正式 Episode 像素。

## 3. Git 与进一步工作

- 所有新增守卫代码与复制脚本位于独立集成工作树 `storyos-main-integration-20261009`，不覆盖仍有大量未提交并发修改的主工作区。
- 按风险边界后续工作：核对 Frame06/24 各自的 Provider Model Receipt、日志、历史 RAW；优先判断 Frame24 是否允许有凭证的非再生技术恢复。随后证明原生 Codex 图片能力、检查 Visual Lock / Reviewer 绑定，再针对经 Authorize 的缺失帧继续生成。
- 保留用户已调校的正式图片和发布素材；无视频生成功能，不引入 OpenCodex 代理。

## 4. 2026-10-09 本地 Runtime 数据库正式切换与复核

- 再次进行 27 张表、4,380 行的主键排序摘要核验时，只发现 `TB_RUNTIME_REVIEW_REQUEST` 存在变化：113 行不增不减，仅 2 条 `story-semantic-critic-shadow` 在目标库已经由 `AWAITING_PRODUCT_REVIEW` 合法推进到 `SUPERSEDED`。这是之前完成的产品审核过期清理，**不是数据复制缺失或 Runtime Worker 写入分叉**。
- 兼容审计脚本新增只读 `verify --allow-shadow-advance`：必须保证其他 26 张 V2 表完全一致，Shadow 的 2 行只允许 `STATUS/PAYLOAD/UPDATE_TIME` 及受限的派生投影字段变化、身份不变、`AWAITING_PRODUCT_REVIEW -> SUPERSEDED`；更多、更少或无关差异均 fail closed。实际结果：`SOURCE_TARGET_VERIFIED_WITH_AUTHORIZED_SHADOW_ADVANCES`，27 表、4,380 行、2 条已授权 Shadow 变更，其他表哈希一致。
- Windows 计划任务 `StoryOSRuntime` 由 SYSTEM 管理。操作前核查无在途正式图片派发任务，完整备份 `.storyos/runtime-launcher/runtime.env` 并校验备份 SHA-256。先停止计划任务并确认 Launcher/Worker/监控子进程都退出，再原子切换唯一 `STORYOS_MYSQL_DB` 值为 `STORY_OS_RUNTIME`，随后重新启动原计划任务。
- 首次尝试因 `File.Replace` 备份路径参数无效而在写入前安全中止，并从原配置重新启动；随后通过无敏感数据的临时文件测试原子替换，清理临时配置文件，重新完成停机切换。
- **切换后实测**：`StoryOSRuntime=Running`，新 Worker PID 为 `2996`，实时 Worker 心跳 `HEALTHY` 且错误数 0；默认 MySQL 连接精确指向 `127.0.0.1:3307/STORY_OS_RUNTIME`，数据库健康检查成功。
- 完整保留源小写数据库。正式新库中依旧有 5 条 Generation Attempt、2 条 `OUTCOME_UNKNOWN` 与 2 条 `SUPERSEDED` Shadow 审核，没有新增图片 Attempt，也没有自动恢复旧未知调用。
- **隔离 TEST_ONLY**：Phase5A Capability Canary 的守卫严格要求 `127.0.0.1:3306/story_os_runtime`；不得把正式 Runtime 的 3307 大写库改回 3306 或将正式 Episode 作为 Canary。

## 5. 原生 Codex Capability 诊断进展

- 真实原生 Runner 在 Windows 用户 Session 1 中健康、签入、可见模型目录。普通登录探测保持 `codex_auth_probe=30` 秒，仅图片工具可见性纯文本探测使用独立 `image_tool_visibility_probe=120` 秒超时。
- 受限实测返回 `transport_probe_status=PASS`，`session_start=PASS`，`image_generation_visible_secondary=true`，`status=READY_FOR_REAL_CAPABILITY_PROOF`，`tool_visibility_evidence_level=SECONDARY_ATTESTATION`；**不是图片生成成功的 Authority**。
- `tool_registry_attestation=UNAVAILABLE`，`tool_capability_state=UNKNOWN`；没有生成正式图片，也没有预占或消耗 Attempt。下一阶段只有符合固定身份和数据库隔离的 TEST_ONLY Canary 可尝试真实 Provider 工具能力证明，不得从 Secondary 直接跳过门禁。

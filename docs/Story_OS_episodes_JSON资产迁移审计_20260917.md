# Story OS episodes JSON 资产迁移审计

日期：2026-09-17

状态：**ACTIVE AUDIT / 作为 JSON → MySQL/Redis/File 分类清单**

## 1. 扫描结论

本轮有两个口径：

- Git tracked `episodes/**/*.json`：**1396** 个；
- 按 `episode_discovery.iter_episode_roots()` 识别的 12 个当前生产 Episode 实体目录扫描：**1408** 个 JSON（包含当前工作区尚未提交的 Episode 数据）。

2026-09-17 存储归属 Registry 完成后，1408/1408 已能确定目标，不再存在 UNKNOWN：

| 目标 | 数量 | 占比 | 说明 |
| --- | ---: | ---: | --- |
| MySQL | 1049 | 74.5% | 长期事实、Contract、Review、Provider Receipt、Workflow/Production/Metric |
| Redis | 64 | 4.5% | next-action、runner/driver、transport、capability、current pointer 等可重建热状态 |
| 文件但退出 active Episode | 295 | 21.0% | 171 worker 本地诊断、73 历史 revision、51 test fixture |
| UNKNOWN | 0 | 0% | 新增未分类 JSON 将由 Registry/测试阻止 |

按旧文件生命周期统计：

- **1077** 个 JSON：完成 MySQL/Redis 切换后停止长期生成/删除兼容文件；
- **36** 个：`EXPORT_ONLY`，只在交付/调试时按需导出，不作为数据库；
- **171** 个：`LOCAL_ONLY` worker/critic 原始诊断，不应长期 Git 跟踪；
- **73** 个：历史 revision，应迁历史归档，不留 active Episode；
- **51** 个：测试 fixture，应迁 `tests/fixtures` 或测试生成目录。

### 1.1 真实存储 Canary（2026-09-17）

本轮已从“代码/单测可用”推进到真实 MySQL / Redis 实例验证：

- MySQL 连接：`121.89.82.216:9000`，MySQL `8.0.46`，数据库 `story_os_runtime`；
- MySQL 兼容检查：`lower_case_table_names=1`；
- V2 Schema 已按显式迁移入口执行，当前识别 **22 张 `TB_*` 表**，全部 `InnoDB`、`utf8mb4_0900_ai_ci`；
- Provider Receipt：`dual` 真写库 → 真读回 → Canary 数据清理，**PASS**；
- Frame Contract：`dual` 真写库 → 真查询 → Canary 数据清理，**PASS**；
- Redis：`NEXT_ACTION / RUNNER_STATE / QUEUE / CIRCUIT_BREAKER / HOST_REQUEST_CURRENT / DRIVER_STATE / DRIVER_HEARTBEAT` 7 类热状态真实写读一致，**PASS**，Canary key 已清理；
- 当前全局默认仍保持 `episode_meta_store=json`、`hot_state=file`，在完成 Runner 环境继承确认与分组提交前不直接切默认值。

环境侧已将 MySQL 连接项写入本地 `.storyos/runtime-launcher/runtime.env` 与 Windows 用户级环境变量；当前已启动的 WebCodex Runner 不会动态刷新父进程环境，因此本轮真实 Canary 由 StoryOS Runtime Launcher 的 allowlist env loader 显式加载。下次 Runner 重启后再验证进程级继承，再决定是否把全局默认切到 `dual`。

因此目标不是“删掉几个 JSON”，而是**让 active Episode 不再长期依赖 JSON 数据库化存储**。

问题不是单个 JSON 大，而是同一 Episode 会同时产生：

- 20 份 Frame Contract；
- 20 份或更多 Frame Review/Scout；
- 多轮 Provider Receipt；
- 多轮 Host Request / Review Request；
- Production Queue/Ledger；
- PREIMAGE Snapshot/Candidate；
- Runtime heartbeat/next-action/circuit-breaker；
- Performance/Observability 快照。

这些数据的生命周期完全不同，不应该继续统一表现为“Episode 目录 JSON”。

## 2. 分类表

| JSON 家族 | 当前角色 | 目标 | 文件是否长期保留 |
| --- | --- | --- | --- |
| `episode-state.json` | Stage 权威 | MySQL `TB_EPISODE_STATE` + History | 迁移完成后否，仅兼容导出 |
| `runtime-checkpoint.json` / `runtime-dag-state.json` | Workflow/Task 状态 | MySQL Workflow/Task/Event | 否 |
| `production-ledger.json` | 生产帧事实 | MySQL `TB_PRODUCTION_FRAME/ATTEMPT` | 否 |
| `production-queue.json` | 当前队列+历史混合 | MySQL durable + Redis hot queue | 否 |
| `provider-receipts/*.json` | Provider 调用回执 | MySQL `TB_PROVIDER_RECEIPT` | 否 |
| `frame-reviews/*.json` | 帧终审 | MySQL `TB_FRAME_REVIEW` | 否 |
| `frame-scouts/*.json` | Scout 结果 | MySQL `TB_FRAME_REVIEW` type=SCOUT | 否 |
| `runtime/contracts/frames/*.json` | Frame Contract | MySQL `TB_FRAME_CONTRACT` | 否 |
| `*-contract.json` | Episode Contract | MySQL `TB_EPISODE_CONTRACT` | 否，必要时导出 |
| `*-review.json` | Story/Visual/Release Review | MySQL `TB_REVIEW_RECORD` | 否 |
| `delegated-approvals.json` 等 | Approval | MySQL `TB_APPROVAL_RECORD` | 否 |
| `host-requests/*.json` | Host Request 历史 | MySQL `TB_HOST_REQUEST` | 否 |
| `product-host-request.json` | 当前 Host Request 指针 | Redis current pointer + MySQL history | 否 |
| `next-action.json` | 当前派生动作 | Redis | 否 |
| `driver*.json` | Driver 心跳 | Redis + Event/Trace | 否 |
| `circuit-breaker.json` | 熔断热状态 | Redis，必要变更写 Event | 否 |
| `effective-config.json` | 派生配置缓存 | Redis/cache，由 config SHA 重建 | 否 |
| `runtime-capabilities.json` | Host 能力缓存 | Redis TTL | 否 |
| `preimage-candidates/*.json` | PREIMAGE Candidate | MySQL Contract/Task | 否 |
| `preimage-*-snapshot.json` | PREIMAGE 版本/Barrier | MySQL Contract/Event | 否 |
| `prompt-packages/*.json` | 生成态 Prompt | MySQL `TB_PROMPT_PACKAGE` | 否，源 Prompt 可留文件 |
| `episode-performance-ledger.json` | 性能账本 | MySQL Event/Trace/Metric | 否 |
| `workflow-observability.json` 等 | 派生观测 | MySQL metric view / API 现算 | 否 |
| `release-manifest.json` | 发布投影 | MySQL Release + Artifact；交付时导出 | EXPORT_ONLY |
| `final-candidate-snapshot.json` | 冻结快照 | MySQL Release/Artifact/SHA | EXPORT_ONLY |
| `character-pixel-master.json` | 图片母版元数据 | MySQL Artifact/Contract；图片本体留 media | JSON 否，图片保留 |
| `character-master-crops.json` | crop manifest | MySQL Artifact relation；图片本体留 media | JSON 否，图片保留 |
| `meta/tests/**/*.json` | 测试 fixture | tests/fixtures 或生成测试数据 | 生产 Episode 不保留 |

## 3. 第一批应迁走的 JSON

优先级 P0（数量多、迁移风险相对低）：

1. `provider-receipts/*.json`；
2. `frame-reviews/*.json`；
3. `frame-scouts/*.json`；
4. `runtime/contracts/frames/*.json`；
5. `runtime/reviews/*.json`；
6. `runtime/host-requests/*.json`；
7. performance / observability 派生快照。

这一批不会先改变 Episode Stage 权威，可以先做 DB 双写并验证，收益最大。

## 4. 第二批迁移

- Episode Contract；
- Story/Visual/Release Review；
- Production Ledger/Attempt；
- Runtime Request；
- PREIMAGE State/Candidate/Snapshot；
- Approval/Release。

## 5. 最后迁移

`episode-state.json` 最后切，因为它当前仍被大量生产代码与历史设计视为阶段事实源。必须先做到：

- MySQL State Repository 可用；
- Event/History 同事务；
- dual-write 对账稳定；
- Runtime 读影子无差异；
- rollback 经过演练。

## 6. 禁止误迁

以下不能因为“想少文件”就塞进 MySQL：

- PNG/JPG/WebP/视频/音频本体；
- 大型发布 ZIP；
- Git 管理的标准、模板、全局配置；
- 需要保留原始字节 SHA 的冻结媒体。

数据库只保存这些文件的 Artifact 元数据和 SHA。

## 7. 新增 JSON 准入规则

从本方案生效后，新写入 `episodes/**/meta/*.json` 必须回答：

1. 为什么不能进 MySQL？
2. 如果只是当前运行态，为什么不能进 Redis？
3. 如果只是派生视图，为什么不能 API/CLI 现算？
4. 它是否必须纳入 Git？

无法回答则默认**不允许新增长期 JSON**。


# Story OS 数据持久化分层与 JSON 瘦身改造方案 V1.0

更新时间：2026-09-18

状态：**ACTIVE DESIGN / 目标是显著减少 Episode JSON，小文件不再承担数据库职责**

## 一、当前事实

本轮仓库扫描得到：

- `docs/`：185 份 Git tracked Markdown；
- `reports/`：86 份 Git tracked Markdown/JSON；
- `episodes/`：1396 个 Git tracked JSON 文件；
- 现有 MySQL Runtime Schema 只有 `event_log / trace_span / artifact_index / platform_latest_record` 等基础表，而且仍是旧小写命名；
- Runtime Repository 仍支持 `jsonl / mysql / dual`，默认兼容 JSONL；
- Redis 已有真实连接适配与健康检查，但尚未成为 Episode 热状态的统一承载层。

当前 `episodes/**/meta` 中同时混放了：权威事实、运行态、派生缓存、Review、Provider 回执、Frame Contract、Prompt Package、性能快照、Host Request。它们本质上属于不同存储类型，却都以 JSON 小文件表现。

进一步按当前 12 个生产 Episode 实体扫描（含未提交工作区 Episode）共有 **1408 个 JSON**；`episode_storage_policy.py` 已实现 1408/1408 归属分类：MySQL 1049、Redis 64、历史/本地诊断/测试文件 295、UNKNOWN=0。

## 二、目标架构

```text
                       ┌─────────────────────┐
                       │      Story OS       │
                       └─────────┬───────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
     ┌────────────────┐ ┌────────────────┐ ┌─────────────────┐
     │ MySQL 事实层    │ │ Redis 热状态层 │ │ 文件/对象存储层  │
     │ authoritative  │ │ rebuildable    │ │ media/source     │
     ├────────────────┤ ├────────────────┤ ├─────────────────┤
     │ Episode/State  │ │ next-action    │ │ 图片/视频/音频   │
     │ Workflow/Task  │ │ heartbeat      │ │ 发布媒体          │
     │ Contract/Review│ │ queue hot view │ │ Story/Prompt源稿  │
     │ Production     │ │ locks/fences   │ │ standards/config │
     │ Receipt/Trace  │ │ circuit breaker│ │                   │
     └────────────────┘ └────────────────┘ └─────────────────┘
```

核心规则：

1. **长期事实进 MySQL。**
2. **为了速度而存在、丢了能重建的进 Redis。**
3. **只有媒体二进制、Git 管理的规范/模板、必要源稿留文件。**
4. 不再为“方便调试”让生产目录永久堆积海量 JSON；调试视图由 CLI/API 按需导出。

## 三、Episode 目录目标形态

迁移完成后，单个 Episode 目录目标缩减为：

```text
episodes/<episode>/
├── README.md                  # 人类入口，可选
├── story/                     # 必要创作源稿，可选 Git 资产
├── prompts/                   # 仅保留人工/长期源 Prompt；生成态 Package 不落长期文件
└── media/
    ├── candidates/
    ├── approved/
    ├── identity/
    └── publish/
```

`meta/*.json` 最终不再作为默认生产持久化目录。兼容期允许生成只读导出，但必须可从 MySQL/Redis 重建，并默认进入忽略目录而不是 Git。

## 四、MySQL 承载范围

### 4.1 权威状态

迁移：

```text
episode-state.json
runtime-checkpoint.json
runtime-dag-state.json
```

目标：

```text
TB_EPISODE
TB_EPISODE_STATE
TB_EPISODE_STATE_HIS
TB_WORKFLOW_RUN
TB_TASK
TB_EVENT_LOG
```

当前 Stage 读取在切换前继续兼容 `episode-state.json`；切换后 MySQL 成为阶段权威，文件只允许作为兼容导出，不能双主。

### 4.2 Contract

迁移：

```text
character-contract.json
character-visual-contract.json
shot-progression-review.json
capture-event-contract.json
world-state.json
temporal-continuity.json
wardrobe-contract.json
voice-contract.json
frame-contract-index.json
runtime/contracts/frames/*.json
```

目标：`TB_EPISODE_CONTRACT` + `TB_FRAME_CONTRACT`。

Contract 的核心查询字段结构化；完整版本体允许保留 `PAYLOAD JSON`，并绑定 `VERSION / SHA256 / SOURCE_SHA256 / STATUS`。

### 4.3 Review / Approval

迁移：

```text
concept-ambition-review.json
story-semantic-review.json
recent5-semantic-review.json
frame-reviews/*.json
frame-scouts/*.json
visual-lock-*.json
release-semantic-review.json
delegated-approvals.json
production-approval.json
```

目标：`TB_REVIEW_RECORD / TB_FRAME_REVIEW / TB_APPROVAL_RECORD`。

### 4.4 Production / Provider

迁移：

```text
production-ledger.json
provider-receipts/*.json
batch-repair-decisions/*.json
production-commit-journal.json
production-reconciliation.json
```

目标：

```text
TB_PRODUCTION_FRAME
TB_PRODUCTION_ATTEMPT
TB_PROVIDER_RECEIPT
TB_ARTIFACT_INDEX
TB_EVENT_LOG
```

这是最优先迁移组之一：目前 Provider Receipt、逐帧 Review、Frame Contract 形成大量小文件。

### 4.5 Runtime / Host Request

迁移长期事实：

```text
runtime-request.json
host-requests/*.json
preimage-task-state.json
preimage-candidates/*.json
preimage-committed-snapshot.json
```

目标：`TB_RUNTIME_REQUEST / TB_HOST_REQUEST / TB_TASK / TB_EPISODE_CONTRACT`。

“当前正在执行哪一条”不在 MySQL 大 payload 上频繁轮询，当前指针放 Redis。

### 4.6 Performance / Observability

迁移：

```text
episode-performance-ledger.json
workflow-performance.json
workflow-observability.json
image-scheduler-performance.json
batch-runtime-performance.json
quota-observability.json
trace-summary.json
```

目标：事件/Trace 原始事实写 `TB_EVENT_LOG / TB_TRACE_SPAN`，需要查询的阶段聚合写 `TB_METRIC_SNAPSHOT`。这些 JSON 以后只作为按需导出的诊断报告。

### 4.7 Validation / Data Review

验证报告需要结构化，但不等于把整篇报告逐字段搬进数据库：

| 内容 | MySQL 结构化事实 | 文件/对象存储 |
| --- | --- | --- |
| `meta/validation/*_validation_report.json` | 验证阶段、最终状态、校验器版本、下一状态、每个 Check 的名称/状态/路径/SHA/失败原因 | 完整原始报告作为可重建导出或证据引用 |
| `meta/preproduction-validation.json` | 验证批次、Episode、状态、检查项结果、绑定源指纹 | 原始报告与人工说明 |
| `meta/post-publish-metrics.json` | 每个 `6h/24h/48h/7d` checkpoint 的观测时间、来源、数值指标、修正标记 | 平台原始导出、截图、采集凭证 |
| `meta/post-publish-review.json` | 最新 checkpoint、关键漏斗数值、计算版本、证据引用 | 人读诊断正文与历史叙述 |

具体落表：门禁验证结果复用 `TB_REVIEW_RECORD`，发布后数值复用 `TB_METRIC_SNAPSHOT`；需要筛选、排序或对账的字段必须是列或子记录，低频检查详情、平台扩展字段和长文本才允许留在小型 `PAYLOAD JSON`。`data-review-state.json` 在 authority cutover 前仍是阶段门禁权威，不能因为结构化而直接删除。

### 4.8 MySQL JSON 行大小硬边界

`PAYLOAD` 不是完整业务文档的存储位置。所有 MySQL JSON 写入口统一执行 **16KB 单行内嵌上限**：

- 小于上限：只保留确实需要随记录读取的低频扩展字段；查询、筛选、对账字段必须使用表列；
- 超过上限：完整文档写入 Runtime Workspace，表内只保留 `projection_type`、版本、来源 SHA/字节数、外部文档相对路径，以及少量业务摘要；
- 读取时按文档 SHA 校验后回读完整文档；外部文档缺失时不得把不完整投影冒充完整事实；
- 迁移脚本与应用写入使用同一规则；已有历史大行必须单独执行“外置完整文档 → 投影回写 → 回读校验”的回填，不与普通 JSON 删除混做。

当前重点投影：Frame Contract、Prompt Package、Runtime Review Request、Metric Snapshot、Approval Record、Release Record。长 Prompt、source 列表、execution session、文件明细和审核 bundle 不再重复塞入 MySQL。

验证报告遵循同一边界：MySQL 只保存验证阶段、状态、Check 名称/状态/路径，以及短 detail；长 detail 只保存 SHA-256、字节数和有限预览，Check 数量过多时退化为总数、PASS/FAIL 计数和整体 SHA。完整报告仍保留为 `meta/validation/*_validation_report.json` 文件证据。

历史回填在 16KB 硬边界之外又执行了 12KB、8KB 两级近阈值清理；当前真实库 23 个 JSON 列在 8KB 阈值下均无超限行。未来新写入仍以 16KB 作为统一拒绝上限，优先写小型投影。

## 五、Redis 承载范围

以下内容属于**热状态**，不应该继续永久写 Episode JSON：

| 当前 JSON/概念 | Redis 目标 |
| --- | --- |
| `next-action.json` | `STORYOS:EP:{ID}:NEXT_ACTION` |
| `driver-beacon.json` / `driver.json` | `STORYOS:EP:{ID}:DRIVER_HEARTBEAT` |
| `circuit-breaker.json` | `STORYOS:EP:{ID}:CIRCUIT_BREAKER` |
| `in-flight-codex.json` | `STORYOS:EP:{ID}:INFLIGHT` |
| 当前 `product-host-request.json` 指针 | `STORYOS:EP:{ID}:HOST_REQUEST_CURRENT` |
| 生产队列 queued/running 视图 | `STORYOS:EP:{ID}:QUEUE` |
| Runtime lock/fence | `STORYOS:LOCK:EP:{ID}:{SCOPE}` |
| 并发 worker/额度计数 | `STORYOS:EP:{ID}:COUNTERS` |
| `effective-config.json` | 配置版本缓存，按 config SHA 重建 |
| `runtime-capabilities.json` | Host/Runtime capability 短期缓存 |

队列历史、Attempt、失败原因仍写 MySQL；Redis 只保存当前工作集。

## 六、文件继续保留什么

必须保留文件/对象存储：

- `media/**` 图片/视频/音频；
- 发布成品；
- Character Pixel Master 与 crop 图像本体；
- Git 管理的 `standards/**`、`config/**`、模板与规范；
- 必要的创作源稿（Story/Storyboard/人工 Prompt）；
- 需要人工交付的最终报告/README。

数据库 `TB_ARTIFACT_INDEX` 只保存路径/URI、SHA、类型、Owner、生成来源和冻结状态。

## 七、迁移顺序

### P0：规范冻结

- 新数据库规范生效；
- 建立 JSON 分类 registry；
- 禁止新增“没有分类”的 Episode JSON。

### P1：MySQL V2 Schema

- 新建符合大写/TB_/0900_ai_ci 的表；
- 旧 `story_os_runtime` 小写表保持只读兼容；
- Repository 增加 V2 实现。

### P2：高数量 JSON 双写

先迁：

1. Provider Receipt；
2. Frame Review / Frame Scout；
3. Frame Contract；
4. Host Request / Runtime Review Request；
5. Performance/Observability。

这些最能立即降低小文件数量，而且不先碰 Stage 权威，风险最低。

### P3：Redis 热状态

- next-action；
- heartbeat/driver；
- locks/fences；
- queue hot state；
- circuit breaker；
- current request pointer。

### P4：Production Ledger / Workflow / Task

把生产当前状态与历史 attempt 切到 MySQL，JSON 仅兼容导出。

### P5：Episode State 权威切换

最后才迁 `episode-state.json`：

```text
JSON authority
  → dual write + consistency check
  → MySQL read shadow
  → MySQL authority
  → JSON export only
  → stop JSON export by default
```

### P6：文件瘦身

- 删除/停止生成可完全重建的 Runtime JSON；
- Episode 目录只保留创作源稿 + media；
- Debug 需要时由 `story_os export/debug` 临时生成快照。

## 八、回滚与安全边界

1. 不做“一次性把 1396 个 JSON 删除”的大爆炸迁移。
2. 每类数据必须经历：双写 → 对账 → 影子读 → 切读 → 停旧写。
3. Redis 永远不能成为审批、Stage、Provider Receipt 的唯一事实源。
4. Media 不进 MySQL BLOB。
5. 任何 MySQL authority 切换必须有一致性扫描和明确 rollback flag。
6. 历史 Episode 不强制回写成新格式；可按需要导入 DB，原始历史证据只读归档。

## 九、最终目标

Story OS 从：

```text
Episode目录 = 小型数据库 + Cache + 日志 + 媒体 + 事实源
```

收敛为：

```text
MySQL = 事实/历史
Redis = 当前热状态
Object/File = 媒体与源资产
Episode目录 = 人类可读入口 + 必要源稿 + 媒体工作区
```

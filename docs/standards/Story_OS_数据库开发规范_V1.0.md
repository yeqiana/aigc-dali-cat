# Story OS 数据库开发规范 V1.0

更新时间：2026-09-17

状态：**ACTIVE / 新增数据库与表结构的唯一命名与 DDL 规范**

## 1. 规范来源与适用范围

本规范基于项目外部输入的《数据库开发规范》改造成 Story OS 专用版本。外部规范的强制项在 Story OS 中保持不变：

- 数据库名、表名、字段名统一使用**大写字母 + 下划线**；
- 业务表统一以 `TB_` 开头；
- 数据库名、表名、字段名长度不超过 32 个字符；
- 普通索引使用 `INDEX_表名_字段名`，唯一索引使用 `INDEX_表名_字段名_UNIQUE`；
- 检查约束、外键、默认约束分别使用 `CHECK_` / `FK_` / `DF_` 前缀；
- 事务在代码方法或事务注释中使用 `TR_表名_操作名称` 标识；
- MySQL 统一 `utf8mb4` + `utf8mb4_0900_ai_ci`；
- 表和字段都必须有业务注释；
- 存储引擎统一 InnoDB。

适用范围：Story OS 新增数据库、表、字段、索引、约束、迁移脚本、Repository 与数据库评审。

## 2. Story OS 数据分层原则

Story OS 不再把 Episode 目录中的大量 JSON 当作长期持久化方案。目标分三层：

| 层 | 角色 | 允许存什么 | 禁止存什么 |
| --- | --- | --- | --- |
| MySQL | 权威事实与历史 | Episode、状态、Workflow、Task、Contract、Review、生产记录、Provider 回执、审批、发布、事件、Trace、Artifact 索引 | 图片/视频二进制、临时心跳、短期锁 |
| Redis | 可重建热状态 | 当前 next-action、Driver 心跳、运行锁、并发计数、熔断状态、当前队列、当前 Host Request 指针、短期缓存 | 唯一历史事实、不可重建审批结果、长期审计记录 |
| 文件/对象存储 | 大文件与 Git 权威资产 | 图片、视频、音频、封面、可发布媒体、标准/模板、必要的 Story/Prompt 源文件 | 可查询的 Runtime 状态、重复 Review JSON、Provider Receipt JSON 海量小文件 |

**原则：MySQL 是事实层，Redis 是速度层，文件系统是媒体/源资产层。Redis 失效后必须可从 MySQL 重建。**

## 3. 数据库命名

新规范逻辑数据库名：

```sql
CREATE DATABASE STORY_OS_RUNTIME
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_0900_ai_ci;
```

注意：当前代码中的 `story_os_runtime` 属历史实现。迁移时必须先检查 MySQL `lower_case_table_names`，禁止只靠“改大小写”做原地迁移。

## 4. 表命名与核心表族

Story OS 新表统一 `TB_` 前缀。首批目标表如下：

| 表 | 用途 |
| --- | --- |
| `TB_PROJECT` | 项目 |
| `TB_EPISODE` | Episode 基础信息 |
| `TB_EPISODE_STATE` | Episode 当前状态 |
| `TB_EPISODE_STATE_HIS` | 状态历史 |
| `TB_WORKFLOW_RUN` | 一次 Workflow 执行 |
| `TB_TASK` | Task/PREIMAGE/Review/Image 任务 |
| `TB_EVENT_LOG` | Event Contract 事实 |
| `TB_TRACE_SPAN` | Trace Span |
| `TB_ARTIFACT_INDEX` | Artifact 元数据与 SHA/路径索引 |
| `TB_EPISODE_CONTRACT` | Episode 级可版本化 Contract |
| `TB_FRAME_CONTRACT` | Frame Contract |
| `TB_REVIEW_RECORD` | Story/Visual/Release 等 Review |
| `TB_FRAME_REVIEW` | 帧级 Review/Scout |
| `TB_PRODUCTION_FRAME` | 每帧生产当前状态 |
| `TB_PRODUCTION_ATTEMPT` | 每次生图/返修尝试 |
| `TB_PROVIDER_RECEIPT` | Provider 回执 |
| `TB_RUNTIME_REQUEST` | Runtime Request |
| `TB_HOST_REQUEST` | Host Request/PREIMAGE Request |
| `TB_APPROVAL_RECORD` | Delegated/Product/User Approval |
| `TB_RELEASE_RECORD` | Release/Snapshot/Publish 记录 |
| `TB_METRIC_SNAPSHOT` | Performance/Quota/Observability 聚合快照 |
| `TB_PROMPT_PACKAGE` | 生成期 Prompt Package |
| `TB_SCHEMA_VERSION` | Schema 版本与迁移审计 |

不要为每一个旧 JSON 文件机械创建一张表。相同领域使用统一表 + `RECORD_TYPE`/`CONTRACT_TYPE` + `VERSION`，核心查询字段必须结构化，低频可演进内容允许使用 MySQL `JSON` 字段。

## 5. 字段规范

字段统一大写：

```sql
EPISODE_ID
CURRENT_STATE
WORKFLOW_RUN_ID
TASK_ID
TRACE_ID
STATUS
VERSION
PAYLOAD
SHA256
CREATE_TIME
UPDATE_TIME
```

要求：

1. ID 字段注释必须说明生成规则。
2. 枚举字段注释必须列出值域。
3. 时间统一使用 `DATETIME(6)`，代码侧统一转换为 UTC 后落库；展示层再转换时区。
4. `CREATE_TIME` / `UPDATE_TIME` 为通用审计字段。
5. 逻辑删除仅用于真正需要“恢复”的业务表；Event、Trace、Attempt 等追加型事实不做软删除。
6. `JSON` 字段只承载低频可演进 payload；凡是需要筛选、排序、JOIN、唯一约束的字段必须拆为正式列。

## 6. 索引与约束

示例：

```sql
CREATE INDEX INDEX_TB_TASK_EPISODE_STATUS
    ON TB_TASK (EPISODE_ID, STATUS);

CREATE UNIQUE INDEX INDEX_TB_EVENT_LOG_EVENT_ID_UNIQUE
    ON TB_EVENT_LOG (EVENT_ID);

ALTER TABLE TB_PRODUCTION_FRAME
    ADD CONSTRAINT CHECK_TB_PRODUCTION_FRAME_NO
    CHECK (FRAME_NO >= 1 AND FRAME_NO <= 999);
```

禁止继续新增 `idx_*` / `uk_*` 小写索引名。

## 7. 注释规范

所有表与字段必须 `COMMENT`。禁止只写“状态”“数据”“扩展字段”这类无业务语义注释。

```sql
CREATE TABLE TB_EPISODE_STATE (
    EPISODE_ID VARCHAR(64) NOT NULL COMMENT 'Episode 业务ID',
    CURRENT_STATE VARCHAR(32) NOT NULL COMMENT '当前生产阶段：IDEA_LOCKED/STORYBOARD_LOCKED/VISUAL_CALIBRATED/PRODUCTION_PASSED/PUBLISH_READY/PUBLISHED/DATA_REVIEWED',
    STATE_VERSION BIGINT NOT NULL DEFAULT 1 COMMENT '乐观锁版本号，每次状态迁移递增',
    UPDATE_TIME DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间，数据库按UTC语义保存',
    PRIMARY KEY (EPISODE_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Episode当前阶段权威状态表';
```

## 8. 事务规范

关键事务必须在方法名或注释中标记：

- `TR_TB_EPISODE_STATE_TRANSITION`：状态迁移 + 历史写入 + Event 记录；
- `TR_TB_PRODUCTION_FRAME_COMMIT`：生产候选提交 + Attempt + Artifact 索引；
- `TR_TB_REVIEW_RECORD_APPLY`：Review 结果 + Frame 状态批量应用；
- `TR_TB_PREIMAGE_AUTHORITY_COMMIT`：PREIMAGE 四候选单写提交。

任何跨表权威变更必须在一个事务内完成，禁止“先改 MySQL、再靠 JSON 补偿”成为永久设计。

## 9. Redis 规范

Redis Key 使用统一前缀：

```text
STORYOS:EP:{EPISODE_ID}:NEXT_ACTION
STORYOS:EP:{EPISODE_ID}:DRIVER_HEARTBEAT
STORYOS:EP:{EPISODE_ID}:CIRCUIT_BREAKER
STORYOS:EP:{EPISODE_ID}:QUEUE
STORYOS:EP:{EPISODE_ID}:HOST_REQUEST_CURRENT
STORYOS:LOCK:EP:{EPISODE_ID}:{SCOPE}
```

要求：

- 所有临时状态必须设置合理 TTL；
- Redis 中不得保存唯一不可重建事实；
- 进程启动/Redis Flush 后可通过 MySQL 当前事实重建；
- Fence/Lock 必须携带 owner/token，禁止只有布尔锁；
- 大 payload 不进入 Redis，只放 ID、摘要、状态和必要热字段。

## 10. 媒体与大对象

图片、视频、音频、ZIP、Contact Sheet 等二进制禁止直接写 MySQL BLOB。

MySQL 只保存：

- Artifact ID；
- 文件/对象存储 URI；
- SHA-256；
- MIME/尺寸/字节数；
- Owner；
- 生成任务/Trace；
- 生命周期与冻结状态。

## 11. Schema Migration

新增迁移目录目标：

```text
platform/repository/mysql/migrations/
```

规则：

1. 每次变更有唯一版本号；
2. 先扩展后切换，禁止直接破坏旧读取；
3. 数据迁移必须支持校验、重跑和回滚；
4. 迁移状态写入 `TB_SCHEMA_VERSION`；
5. 大规模 JSON → MySQL 迁移先双写/对账，再切读，最后停旧 JSON；
6. 不修改历史审计数据来“适配”新 schema。

## 12. 现有实现的兼容结论

当前 `platform/repository/mysql/schema.py` 仍存在：

- 数据库名 `story_os_runtime`；
- 表名 `event_log / trace_span / artifact_index / platform_latest_record`；
- 字段与索引小写；
- `utf8mb4_unicode_ci`。

这些全部标记为 **LEGACY_SCHEMA**。本规范生效后：

- 不再按旧风格新增表或字段；
- 不做危险的原地批量 rename；
- 通过 V2 Schema + 双写 + 一致性校验迁移到新规范；
- 切换完成后再删除旧 schema 兼容路径。

## 13. PR 快速检查

| 检查项 | 强制要求 |
| --- | --- |
| 数据库/表/字段 | 大写下划线 |
| 表前缀 | `TB_` |
| 字符集 | `utf8mb4` |
| Collation | `utf8mb4_0900_ai_ci` |
| 注释 | 表/字段全部有 COMMENT |
| 索引 | `INDEX_...` |
| 约束 | `CHECK_/FK_/DF_` |
| 事务 | `TR_...` 标识 |
| JSON 列 | 仅低频可演进 payload |
| Redis | 只存可重建热状态，有 TTL |
| 大文件 | 文件/对象存储，DB 只存索引/SHA |


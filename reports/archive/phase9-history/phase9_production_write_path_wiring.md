# Phase 9 - P9.27.4 Production Write Path Wiring

日期：2026-09-10
分支：story-platform-v3
范围：把 Runtime 事实写入链路真正接到 repository（Legacy JSONL / MySQL / 双写），并统一 Runtime 内部时间口径
验证方式：本机 Python 3.12.10 + pymysql 1.4.6 + redis-py 8.0.1；真实实例 MySQL 121.89.82.216:9000（8.0.46 / utf8mb4 / 库 story_os_runtime）、Redis 127.0.0.1:6379（AOF 已开启）

## 结论

P9.27 第四批完成：Runtime 的 Event / Trace / Artifact 三类事实不再"只构造不落库"。

- 存储位置由单一环境变量 `STORYOS_RUNTIME_STORE_MODE` 决定：`jsonl`（默认，行为与 Phase 0 一致）/ `mysql` / `dual`；非法值直接 ValueError，不做静默降级。
- 三个 Observer 与 RuntimeAdapter 都能显式注入 repository；`RuntimeAdapter.from_env()` 按环境装配并负责关闭自建连接。
- Runtime 内部时间口径收敛到 `platform.core.clock`，不再同时存在 `datetime.utcnow()` 与 `datetime.now(timezone.utc)` 两套写法。
- 真实 MySQL + Redis 端到端 53 项检查全部通过；期间发现并修复了一个会让一致性校验"说假话"的真缺陷（见第 6 节）。

## 1. 模式矩阵

| 环境变量值 | 写入行为 | 需要 pymysql | 说明 |
| --- | --- | --- | --- |
| `jsonl`（未设置时的默认） | 只写 Legacy JSONL | 否 | 与 Phase 0 行为一致；模块顶层不导入 MySQL 依赖链 |
| `mysql` | 只写 MySQL | 是 | 真实持久化，不落 JSONL |
| `dual` | Legacy JSONL + MySQL 双写 | 是 | `secondary_enabled=False` 可只回滚 MySQL 侧，Legacy 不受影响 |

其他环境变量：`STORYOS_RUNTIME_JSONL_ROOT`（默认 `.storyos`）、`STORYOS_MYSQL_HOST/PORT/USER/PWD/DB`。凭据只从运行环境读取，不写入仓库任何文件。

## 2. 接线前后对比

| 位置 | 接线前 | 现在 |
| --- | --- | --- |
| `EventObserver.record()` | 只构造 EventContract 返回，不落库 | 契约交给注入的 repository 落库；未注入时保持"只观察" |
| EventObserver 的 repository | 没有默认实现，双写只存在于测试和验证脚本 | 由 `RuntimeRepositoryProvider` 按模式装配 |
| `TraceObserver` / `ArtifactObserver` | 只有 `start()` / `register()`，没有持久化入口 | 新增 `save(entity)`，可被 AgentRuntime 的 `trace_sink` 直接调用 |
| `RuntimeAdapter.record_event/trace/register_artifact` | 把契约对象当成 `record()` 的事件类型参数传入（旧 bug） | 直接持久化契约本身，语义正确 |
| Runtime 时间 | `datetime.utcnow()` 与 `datetime.now(timezone.utc)` 并存 | 统一走 `platform.core.clock`，naive UTC 墙钟值 |
| Repository 契约 | 只有 Event 有 Protocol | Trace / Artifact 补齐对称 Protocol |

新增文件：`platform/core/clock.py`、`platform/repository/trace_repository.py`、`platform/repository/artifact_repository.py`、`platform/repository/runtime_repository_provider.py`。

## 3. 真实实例端到端验证

真实 MySQL + Redis，共 53 项检查，0 失败。脚本只写系统临时目录，探测行结束后删除；三表基线 0/0/0，结束时回到 0/0/0。

| 分组 | 覆盖 | 结果 |
| --- | --- | --- |
| A 连接与 DDL | 探活 8.0.46 / 库名 / utf8mb4 / 建库建表幂等 | 5/5 |
| B dual 写入 | Event、Trace、Artifact 各落一行 MySQL，同时各落一行 JSONL；落库时间为无时区墙钟值 | 7/7 |
| C 单条一致性 | 三个主键 Legacy vs MySQL 全部 MATCH，payload/metadata hash 一致 | 3/3 |
| D mysql 模式 | 只写 MySQL，不生成任何 JSONL 文件 | 2/2 |
| E 回滚开关 | `secondary_enabled=False` 时 MySQL 无行、Legacy 正常 | 2/2 |
| F 同主键覆盖 | Trace RUNNING 落库后由 SUCCESS 同主键覆盖，MySQL 仍是单行且状态/耗时正确 | 4/4 |
| G dual 巡检 | 探测行 MATCH；无 legacy_only / mismatch；mysql 模式多出的行被正确报为 mysql_only 异常 | 7/7 |
| H RuntimeAdapter | `from_env()` 双写三类契约，旧 bug 已消除，`close()` 释放自建连接 | 7/7 |
| I adapter 巡检 | adapter 自己的 Legacy 目录与 MySQL 比对全部 MATCH | 3/3 |
| J Redis | ping、首个持有者拿到 Episode 锁、第二个被拒、payload 正确、`release` 后清键、DBSIZE 回到基线、AOF `aof_enabled=1` 且 `aof_last_write_status=ok` | 10/10 |
| K 清理 | 三表行数回到基线 | 3/3 |

实测关键行（dual 模式）：

    event_log      evt_c09f98...     TASK_STARTED   TASK           occurred_at=2026-09-10 13:50:02.022339
    trace_span     trace_a82545...   span_67b4ce...  p9.27.e2e     RUNNING -> SUCCESS  duration_ms=12
    artifact_index artifact_82ba61... IMAGE         probe/e2e7877d7e64b.png

## 4. 语义边界（必须知道）

- 双写失败语义：先写 Legacy 再写 MySQL。MySQL 抛异常时异常向上传播，此时 Legacy 已经落盘。这是刻意的"零静默降级"，代价是可能出现"Legacy 有、MySQL 无"的行，需要靠巡检 `compensating_write` 补偿，而不是靠吞掉异常。
- 覆盖语义不同：Legacy JSONL 是追加写（同一主键可能多行），MySQL 是 upsert（单行）。两侧都按 last-wins 解释，结果一致，但 JSONL 会持续增长，需要归档/压缩策略。
- 默认仍是 `jsonl`：不显式设置环境变量时不会落 MySQL。生产切换属于 Phase 8 生产切换决策范围，本批只把链路接通，不改变默认行为。
- Redis 锁无 TTL：`EpisodeLockManager.acquire` 走 `SET NX` 但不设过期时间，持锁进程崩溃会留下死锁（既有实现，本批未改动，仅记录）。

## 5. 测试

tests/platform 全量：193 passed / 0 failed。

本批新增：

| 文件 | 数量 | 覆盖 |
| --- | --- | --- |
| tests/platform/test_core_clock.py | 7 | naive UTC 语义、ISO 输出、`to_naive_utc` 兼容性、Runtime 事实源码不得残留 `datetime.utcnow()` |
| tests/platform/test_runtime_repository_provider.py | 14 | 三种模式、非法模式报错、惰性导入 MySQL 依赖链、双写与回滚开关、连接归属、健康检查 |
| tests/platform/test_runtime_write_path_wiring.py | 8 | 三个 Observer 落库、未注入时只观察、adapter 接线与 `from_env`、AgentRuntime trace_sink 覆盖 |

## 6. 本批发现并修复的缺陷

JSONL `read_by_id` 口径错误（真实端到端暴露）：

Trace 的 RUNNING 先落一次、完成态用同一主键再落一次。此时全量巡检 `_collect` 是 last-wins，判定 MATCH；而单条比对 `read_by_id` 是 first-wins（返回第一条 RUNNING），判定 MISMATCH。同一个一致性工具对同一份数据给出相反结论，而 RUNNING -> SUCCESS 是正常执行流程，不是异常场景。

端到端 F4 复现后修正：三个 JSONL Store 的 `read_by_id` 全部改为 last-wins，与巡检口径对齐，并补了 4 个回归测试（含真实 `JsonlTraceStore` 加假 MySQL 仓储的覆盖场景）。

## 7. 仍未完成

- 巡检未调度化：没有常驻任务与告警接入，`mysql_only` / `legacy_only` / `MISMATCH` 目前只能在人工执行时被发现。
- 悬停 RUNNING 行没有告警：MySQL 保留 RUNNING 是"已开始未结束"的真实信号，但还没有巡检规则去识别它。
- 数据库账号仍是 `root@%` + GRANT OPTION；与 nacos_config 等库共用实例，生产需要隔离与受限账号。
- Redis 本机、MySQL 远端，实例割裂；`allkeys-lru` 仍可能驱逐 Episode 锁键。
- `ON DUPLICATE KEY UPDATE ... VALUES()` 仍是 8.0 弃用语法，可迁移到 row-alias 写法。
- `platform/repository/dual_write_repository.py`（旧单文件）与 `platform/repository/dual_write/`（新包）同名冲突：Python 实际导入的是包，旧文件仍在仓库中，属既有状态，本批未动，建议后续单独清理。
- 真实生产流量未接入：本批验证全部使用探测数据，生产 Trace/Event 量级下的分页与巡检性能尚未压测。

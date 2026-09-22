# Phase 9 - P9.27 Production Data Foundation

日期：2026-09-10
分支：story-platform-v3
验证方式：本机 Python 3.12.10 + pymysql 1.4.6，真实实例 121.89.82.216:9000（MySQL 8.0.46 / utf8mb4）

## 结论

P9.27 第一批完成：Runtime 数据层的连接管理从“单连接懒连接”升级为“每线程独立连接 + 断连自动重连 + 真实健康检查”；写入路径统一 naive UTC 时间约定；Repository 增加 keyset 分页流式读取，巡检不再依赖一次性全表载入。真实实例 8 项验证全部通过，其中断连重连用真实 `KILL` 复现。

## 1. 连接管理（P9.27.1）

| 能力 | 实现 |
| --- | --- |
| 并发安全 | 每线程独立连接（pymysql Connection 非线程安全，不能跨线程复用） |
| 断连恢复 | 错误码 2006 / 2013 / 2055 自动重连并重试一次；其他异常不重试，直接抛出 |
| 健康检查 | `health_check()` 返回 alive / version / database / charset / time_zone |
| 关闭 | `close()` 幂等，关闭后再次使用会自动重建连接 |
| 事务 | `transaction()` 仍在同一线程连接上切换 autocommit，rollback 语义不变 |

明确边界：这是“每线程连接”，不是连接池。没有连接数上限与空闲回收；长期驻留进程若持续新建线程，需要上层控制线程数量。引入 DBUtils 等池化库属于新增依赖，本阶段不做。

## 2. 时间约定（P9.27.2）

约定：**所有落库时间为 naive UTC 墙钟值**。

`MySqlConnection` 在执行语句前统一把 aware datetime 转成 naive UTC，显式替代此前 pymysql 隐式丢弃 tzinfo 的行为。这解决了 P9.26.6 记录的时间比对歧义：写入侧与校验侧现在使用同一条约定。

实测：以 Asia/Shanghai 的 `2026-09-10 20:34:56.789012+08:00` 写入，落库读出为 `2026-09-10 12:34:56.789012`。

## 3. 分页流式读取（P9.27.3）

三个 MySQL Repository 增加 keyset 分页 `iter_all(batch_size=500)`：

| 表 | 分页键 | 语句形态 |
| --- | --- | --- |
| event_log | event_id | `WHERE event_id > %s ORDER BY event_id LIMIT %s` |
| trace_span | (trace_id, span_id) | `WHERE (trace_id, span_id) > (%s, %s) ORDER BY trace_id, span_id LIMIT %s` |
| artifact_index | artifact_id | `WHERE artifact_id > %s ORDER BY artifact_id LIMIT %s` |

`RuntimeConsistencyScan` 优先使用 `iter_all`，仓储没有该能力时退回 `list_all`，既有调用与测试不受影响。`list_all()` 语义未变。

## 4. 真实实例验证

基线三表为空表。真实实例 8 项检查，0 失败：

| 检查 | 结果 |
| --- | --- |
| health_check 探活 | alive=True，8.0.46 / story_os_runtime / utf8mb4 / time_zone=SYSTEM |
| 真实断连重连 | 另一条连接 `KILL 1480` 后自动重连为 1482，查询成功 |
| aware 时间归一化 | 上海时区 20:34:56.789012+08:00 落库为 12:34:56.789012 |
| Event keyset 分页完整性 | 13/13 条完整、无重复、全局有序 |
| Trace 复合主键分页 | 4/4 span 按 (trace_id, span_id) 完整返回 |
| 事务回滚 | 块内抛错后数据未落库 |
| 探测数据清理 | 三表行数回到 0/0/0 |

## 5. 测试

tests/platform 全量：150 passed / 0 failed（137 + 连接加固 8 + 分页 4 + 巡检流式 1）。

新增：

- tests/platform/test_mysql_connection_hardening.py
- tests/platform/test_mysql_repository_paging.py

## 6. 仍未完成

- Redis：已在本机真实实例完成 Redis Initialization 验证（Windows 服务 Redis，开机自启，127.0.0.1:6379），见 phase9_redis_initialization_validation.md。远端 121.89.82.216:6379 仍不可达；本机实例为 allkeys-lru 淘汰策略，运行时状态键存在被驱逐风险，待确认后再调整。
- 数据库账号：仍是 root@% + GRANT OPTION，正式接入需要受限账号并收敛来源 IP。
- 实例共享：与 nacos_config 等库共用一个实例，生产需评估隔离。
- 弃用语法已收敛（P9.27.5 取代本条旧描述）：三个 MySQL Repository 的 upsert 已由 `VALUES(col)` 迁移为 `AS new` row-alias + `col=new.col`；见 reports/phase9_data_foundation_hardening.md。
- 生产写入链路已接线（P9.27.4 取代本条旧描述）：三个 Observer 与 RuntimeAdapter 都可注入 repository，`RuntimeAdapter.from_env()` 按 `STORYOS_RUNTIME_STORE_MODE` 装配，默认仍是 jsonl；见 reports/phase9_production_write_path_wiring.md。
- 巡检未调度化：没有常驻任务与告警接入。
- 时间约定已收敛（P9.27.4 取代本条旧描述）：Runtime 事实链路统一走 `platform.core.clock` 的 naive UTC，不再保留 `datetime.utcnow()` 与 `datetime.now(timezone.utc)` 两套写法。
- 本报告是 P9.27 第一至第三批的快照；第四批（写入链路接线）见 reports/phase9_production_write_path_wiring.md，第五批（弃用语法收敛 + 巡检调度入口）见 reports/phase9_data_foundation_hardening.md。


---

## 7. 基线推进说明（P9.27.5，2026-09-10 追加）

上文第 5 节的测试数为当批快照，不回改。本批把 tests/platform 基线推进到 **211 passed / 0 failed**，tests/system 仍为 186 passed + 16 subtests，合计 **397 passed + 16 subtests**。

本批新增/变更：

- 三个 MySQL Repository 的 upsert 迁移到 row-alias 写法（`platform/repository/mysql/mysql_event_repository.py`、`platform/repository/trace/mysql_trace_repository.py`、`platform/repository/artifact/mysql_artifact_repository.py`）。
- 新增 `scripts/phase9_consistency_scan.py`：一致性巡检的可调度 CLI 入口，支持 `--entity` / `--compensate` / `--evidence-file`，退出码 0/2/3。
- 新增 `tests/platform/test_phase9_consistency_scan_script.py`（10 例）与 `tests/platform/test_mysql_upsert_row_alias.py`（2 例）。

真实实例端到端：11 项检查 0 失败（含旧写法触发 1287 告警、新写法无告警、mismatch/mysql_only 判定 exit 2、探测数据清理回 0）。

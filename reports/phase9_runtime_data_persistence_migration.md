# Phase 9 - P9.26.4 Runtime Data Persistence Migration

日期：2026-09-10
分支：story-platform-v3
验证方式：本机 Python 3.12.10 + pymysql 1.4.6，真实实例 121.89.82.216:9000

## 结论

P9.26.4 完成：三个 MySQL Repository 已从占位实现替换为真实 SQL 持久化，专属 schema 已建，Event / Trace / Artifact 的 create、query、update（幂等 upsert）、transaction rollback 在真实 MySQL 上全部实测通过。

## 1. 数据模型（DDL）

新建专属库 story_os_runtime（utf8mb4 / utf8mb4_unicode_ci），三张表：

| 表 | 主键 | 用途 |
| --- | --- | --- |
| event_log | event_id | 平台事件事实 |
| trace_span | (trace_id, span_id) | 执行链路 Trace/Span |
| artifact_index | artifact_id | 生产资产索引 |

关键列类型：enum 存 VARCHAR（.value），dict 存 JSON，时间存 DATETIME(6)，sha256 存 CHAR(64)，均有聚合/时间/owner 等二级索引。

## 2. 代码改动

新增：

- platform/repository/mysql/mysql_connection.py —— MySqlConnection 适配器（pymysql 懒连接、execute/query_one/query_all、transaction 上下文、autocommit 控制）
- platform/repository/mysql/schema.py —— 幂等建库建表 apply_schema()

改写（占位 -> 真实 SQL）：

- platform/repository/mysql/mysql_event_repository.py
- platform/repository/trace/mysql_trace_repository.py
- platform/repository/artifact/mysql_artifact_repository.py

每个 Repository 增加 save()（ON DUPLICATE KEY UPDATE 幂等 upsert）与 get()（按主键查询）。无生产调用方，改动不影响既有运行链路。

## 3. 配置（凭据不落盘）

| 环境变量 | 默认 |
| --- | --- |
| STORYOS_MYSQL_HOST | 127.0.0.1 |
| STORYOS_MYSQL_PORT | 3306 |
| STORYOS_MYSQL_USER | root |
| STORYOS_MYSQL_PWD | 无默认，运行时从环境读取 |
| STORYOS_MYSQL_DB | story_os_runtime |

## 4. 真实实例集成验证（实测）

| 项 | 结果 |
| --- | --- |
| 建库建表 apply_schema | OK（3 表创建） |
| Event save + get | 通过 |
| Event 幂等 upsert | 同 id 二次写入 count=1，字段已更新 |
| Trace save + get | 通过 |
| Artifact save + get | 通过 |
| transaction rollback | 通过（回滚后 count=0） |
| 探测数据清理 | 完成（三表空表） |

## 5. 测试

tests/platform：125 passed / 0 failed（原 118 + 本次新增/扩展 7）。

## 6. 已知限制（后续阶段处理）

- 连接池：P9.27 已完成“每线程独立连接 + 断连自动重连 + 健康检查”，仍未引入连接池（无上限与空闲回收），见 phase9_production_data_foundation.md。
- 账号：root@% + GRANT OPTION 权限过宽，正式接入需换受限账号并收敛来源 IP。
- 实例：共享实例（含 nacos_config / daily_event_draw），生产数据基础阶段需评估隔离。
- ON DUPLICATE KEY UPDATE 使用 VALUES() 函数（8.0 已弃用但可用），后续可迁移到 row-alias 语法。
- Repository 尚未接入任何生产写入链路。JSONL 双写（P9.26.5）与一致性校验（P9.26.6）已完成，见 phase9_runtime_data_dual_write_migration.md 与 phase9_runtime_data_consistency_verification.md。

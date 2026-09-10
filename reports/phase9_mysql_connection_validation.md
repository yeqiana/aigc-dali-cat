# Phase 9 - P9.26.3.5 MySQL Connection Validation

日期：2026-09-10
分支：story-platform-v3
验证方式：本机 Python 3.12.10 + pymysql 1.4.6（只读验证 + 会话级临时表 CRUD，无持久写入）

## 结论

连接验证 PASS，但必须把三层分开看，不能混为一谈：

1. 连接层：可连通、凭据有效、CRUD + 事务回滚能力实测通过。
2. Repository 层：仍是占位实现，未接真实 SQL，Event/Trace/Artifact 的 create/query/update/rollback 尚不可验证。
3. Schema：目标实例上没有 Story OS 专属库/表，且该实例是已在使用中的共享实例。

## 1. 连接方式与地址

- 对外地址：121.89.82.216:9000
- 内部身份：MySQL 8.0.46 Community Server，容器主机名 76de00a04c2b，内部端口 3306（对外映射为 9000）
- 驱动：pymysql 1.4.6，charset=utf8mb4，connect/read/write timeout 均为 10s

## 2. 版本与实例身份

| 项 | 值 |
| --- | --- |
| VERSION | 8.0.46 |
| version_comment | MySQL Community Server - GPL |
| hostname | 76de00a04c2b |
| server_id | 1 |
| 内部端口 | 3306 |

## 3. 字符集

| 项 | 值 |
| --- | --- |
| character_set_server | utf8mb4 |
| collation_server | utf8mb4_unicode_ci |
| client / connection / results | utf8mb4 |
| 既有业务表排序规则（daily_event_draw） | utf8mb4_general_ci |

## 4. 时区

- global.time_zone = SYSTEM
- session.time_zone = SYSTEM
- system_time_zone = UTC

## 5. 权限

当前账号 root@%（来源 IP 111.19.41.225），拥有全库全权限，含 GRANT OPTION、CREATE TEMPORARY TABLES、CREATE/DROP/ALTER 等，属超级权限账号。

风险提示：root@% 且带 GRANT OPTION 权限过宽，正式接入应改用受限账号并收敛来源 IP。

## 6. 连接耗时

- 第 1 次（冷连接）：3254.7 ms
- 第 2 次：152.0 ms
- 第 3 次：150.8 ms

冷连接 3.2s 偏高，疑似首次 TCP/认证握手开销；稳定连接约 150ms。

## 7. 关键参数

| 项 | 值 |
| --- | --- |
| sql_mode | ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION |
| max_connections | 151 |
| transaction_isolation | REPEATABLE-READ |
| autocommit | 0（pymysql 默认关闭） |

## 8. 现有 schema 盘点

系统库：information_schema / mysql / performance_schema / sys

业务库：

- daily_event_draw（3 张表：tb_draw_record=12、tb_event=500、tb_user=0）—— 疑似既有抽奖/事件活动应用，非 Story OS schema
- nacos_config（标准 Nacos 配置表）—— 与 yopu-cloud-platform 共享

未发现 Story OS 专属 schema（无 story_os / runtime / event / trace / artifact 库）。

## 9. Repository 层现状（重要）

三个 MySQL Repository 均为占位实现，无真实 SQL：

| 文件 | 现状 |
| --- | --- |
| platform/repository/mysql/mysql_event_repository.py | save() 仅调用 connection.insert_event(asdict(event))，无真实 INSERT |
| platform/repository/trace/mysql_trace_repository.py | save() 仅调用 connection.insert_trace(asdict(trace))，无真实 INSERT |
| platform/repository/artifact/mysql_artifact_repository.py | save() 仅调用 connection.insert_artifact(artifact)，无真实 INSERT |

缺失项：连接抽象、事务边界、连接池策略、charset/timezone 显式配置。所谓 connection 是注入对象，其 insert_event / insert_trace / insert_artifact 方法尚不存在，无法对真实 MySQL 执行。

## 10. 连接层 CRUD + 回滚验证（实测）

在会话级 TEMPORARY TABLE（断开即消失，无持久 DDL）上验证：

| 步骤 | 结果 |
| --- | --- |
| CREATE TEMPORARY TABLE | OK |
| INSERT 2 行 | OK（SELECT COUNT = 2） |
| UPDATE | OK（name 变更为 alpha_updated） |
| ROLLBACK | OK（SELECT COUNT = 0） |
| DROP TEMPORARY TABLE | OK |

说明：连接层 create / insert / select / update / rollback 全部通过；这是裸连接能力，不等于 Repository 层已具备持久化。

## 11. 异常处理

- 首次探测使用 LIKE '%...%' 触发 pymysql 格式化占位符冲突（TypeError），已改用参数化查询修正。
- 未 USE 数据库时 CREATE TEMPORARY TABLE 报 1046 No database selected，已通过 USE 后重试修正。

## 结论与下一步

P9.26.3.5 MySQL Connection Validation：连接层 PASS。

进入 P9.26.4 Runtime Data Persistence Migration 的硬前提：

1. 创建 Story OS 专属 schema 与 event / trace / artifact 表（当前 DDL 尚未存在）。
2. 实现真实 MySQL connection adapter（pymysql 连接池 + charset=utf8mb4 + 时区 + 事务边界），替换三个占位 Repository 的 insert_* 调用。
3. 评估复用共享实例还是独立实例；当前实例已被 nacos_config / daily_event_draw 占用，root@% 权限过宽。

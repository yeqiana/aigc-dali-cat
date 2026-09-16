# Phase 9 - Redis Persistence Enablement (AOF)

日期：2026-09-10
分支：story-platform-v3
范围：只开启 AOF 持久化，其他配置保持原样（用户指令：「开启redis持久化，目前就按这种方式」）
验证环境：本机真实 Redis 127.0.0.1:6379（Windows 服务 Redis，8.10.1 standalone）+ redis-py 8.0.1

## 结论

Redis AOF 持久化已开启，并完成三层验证：

- 运行时已生效：`CONFIG SET appendonly yes` 之后 `aof_enabled=1`，AOF 目录 `D:\soft\redis\data\appendonlydir` 已生成。
- 断电可恢复：把 AOF 目录复制到独立实例重放，写入的值和 TTL 都存活，12 项检查 0 失败。
- 重启后仍生效：Windows 服务的启动命令明确读取 `D:\soft\redis\redis.conf`，该文件已经是 `appendonly yes`；用同一份配置文件起独立实例，解析结果也是 `appendonly=yes`。

未改动项：RDB 快照（save 3600 1 / 300 100 / 60 10000）、`maxmemory 1gb`、`maxmemory-policy allkeys-lru`、`bind 127.0.0.1`、无密码、`appendfsync everysec`。

## 1. 改动清单

| 项 | 改动前 | 改动后 |
| --- | --- | --- |
| `D:\soft\redis\redis.conf` 第 28 行 | `appendonly no` | `appendonly yes` |
| 同文件第 27 行注释 | `# AOF disabled for local dev` | `# AOF enabled for local dev (2026-09-10)` |
| 当前运行实例 | AOF 未启用 | `CONFIG SET appendonly yes`（立即生效，无需重启） |

备份：`D:\soft\redis\redis.conf.bak-20260910`（原文件 700 字节，2026-09-10 20:07:33）。改后文件 701 字节（21:31:30）。

`D:\soft\redis` 在仓库之外，不受 Git 影响，也没有任何密码进入仓库或被提交。

## 2. 运行时生效证据

`CONFIG SET appendonly yes` 返回 OK 之后：

| 检查 | 实测 |
| --- | --- |
| `CONFIG GET appendonly` | yes |
| `CONFIG GET appendfsync` | everysec |
| `aof_enabled` | 1 |
| `aof_last_write_status` | ok |
| `aof_last_bgrewrite_status` | ok |
| `aof_rewrites` | 1 |
| `rdb_last_bgsave_status` | ok（RDB 未受影响） |
| `aof_current_size` / `aof_base_size` | 480 / 89 |

`D:\soft\redis\logs\redis.log`（服务 pid 2042）在同一时刻记录：

    ... * Creating AOF incr file temp-appendonly.aof.incr on background rewrite
    ... * Background AOF rewrite terminated with success
    ... * Successfully renamed the temporary AOF base file temp-rewriteaof-bg-2057.aof into appendonly.aof.1.base.rdb
    ... * Successfully renamed the temporary AOF incr file temp-appendonly.aof.incr into appendonly.aof.1.incr.aof
    ... * Background AOF rewrite finished successfully

## 3. 落盘证据

`D:\soft\redis\data\appendonlydir`：

| 文件 | 大小 | 说明 |
| --- | --- | --- |
| `appendonly.aof.1.base.rdb` | 89 B | AOF base（RDB 前言格式，空数据集） |
| `appendonly.aof.1.incr.aof` | 391 B | 增量 AOF，含探测键的写入与删除记录 |
| `appendonly.aof.manifest` | 102 B | AOF 清单，正确列出上面的 incr 文件 |

写入探测键并等待 `everysec` 落盘后，`appendonly.aof.1.incr.aof` 内容可检索到 `p9probe:aof`。

## 4. 断点重放验证（核心证据）

步骤：向真实实例写入 `p9probe:aof=durable-value` 与 `p9probe:aof:ttl=ttl-value`（TTL 600s）→ 等待 everysec 落盘 → 复制整个 `data` 目录 → 用副本启动独立实例（端口 6381，`--appendonly yes`）→ 检查重放结果 → 关闭临时实例 → 清理探测键。

| 检查 | 结果 |
| --- | --- |
| live `aof_enabled == 1` | PASS |
| live `aof_last_write_status == ok` | PASS |
| live `aof_last_bgrewrite_status == ok` | PASS |
| live `rdb_last_bgsave_status == ok` | PASS |
| live `appendfsync == everysec` | PASS |
| manifest 列出 incr aof | PASS |
| incr aof 含探测键 | PASS |
| 临时实例 6381 启动成功 | PASS |
| 重放后 `p9probe:aof == durable-value` | PASS |
| 重放后 TTL 存活（596s） | PASS |
| 重放后 `dbsize == 2` | PASS |
| 清理后 keyspace 回到基线 0 | PASS |

合计 12 项，0 失败。

## 5. 重启后仍生效的证据

`sc.exe qc Redis`：

    BINARY_PATH_NAME    : "D:\soft\redis\RedisService.exe" run -c "D:\soft\redis\redis.conf" --port 6379 --dir "D:\soft\redis\data"
    START_TYPE          : AUTO_START
    SERVICE_START_NAME  : LocalSystem

服务每次启动都会读 `D:\soft\redis\redis.conf`，而该文件的 AOF 指令已确认是 `yes`。

用同一份配置文件启动独立实例（端口 6382/6383，并把 `dir` / `logfile` / `dbfilename` 覆盖到临时目录，避免和 6379 抢同一份数据文件），解析结果：

    CONFIG GET -> {'appendonly': 'yes', 'appendfsync': 'everysec', 'maxmemory-policy': 'allkeys-lru'}

同时在临时目录里建出了 `appendonlydir`，说明 AOF 是由配置文件打开，不是命令行临时参数。

本机 `redis-server.exe` 是 MSYS 构建，直接把 `D:/soft/redis/redis.conf` 当位置参数会报 `can't open config file '/soft/redis/D:/soft/redis/redis.conf'`，必须以 `./redis.conf`（cwd 为 `D:\soft\redis`）方式传参。这是本机 MSYS 路径转换的怪癖，不影响 Windows 服务：`RedisService.exe` 自己处理配置文件路径，当前服务运行正常。

## 6. 清理与残留检查

- 端口监听：只剩 6379，临时实例 6381/6382/6383 全部关闭
- `p9probe*` 键：已删除，`DBSIZE` 回到基线 0
- 临时目录与临时脚本：已删除，`%TEMP%` 无残留

## 7. 回归测试

`tests/platform`：161 passed / 0 failed（0.68s）。

本次改动只涉及仓库外的 Redis 配置文件，仓库代码未改，测试数量与上轮一致。

## 8. 未改动项与边界

- `maxmemory 1gb` + `maxmemory-policy allkeys-lru`：保持原样。风险仍在：内存压力下 Episode 锁键可能被驱逐，锁丢失意味着同一 Episode 可能被两个 Runtime 同时执行。可选方案（本轮未执行）：状态键独立逻辑库 + `noeviction`，或 `volatile-lru` 加强制 TTL。
- `bind 127.0.0.1`、无密码：保持原样。Runtime 的 MySQL 在远端 121.89.82.216，Redis 在本机，数据层部署仍然割裂。
- `appendfsync everysec`：进程被强杀或整机断电最多丢约 1 秒写入；正常关闭不丢。这是 everysec 的既有语义，本轮没有改成 always。
- 生产写入链路仍未接线：Event / Trace / Artifact 还没有默认接上 Redis / MySQL 仓库，本次只验证存储侧能力。

## 9. 复现命令

    D:\soft\redis\redis-cli.exe -p 6379 config get appendonly
    D:\soft\redis\redis-cli.exe -p 6379 info persistence
    Get-ChildItem D:\soft\redis\data\appendonlydir
    sc.exe qc Redis
    Restart-Service Redis   # 需要管理员；重启后 AOF 由配置文件生效


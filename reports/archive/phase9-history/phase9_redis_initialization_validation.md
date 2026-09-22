# Phase 9 - Redis Initialization Validation

日期：2026-09-10
分支：story-platform-v3
验证方式：本机 Python 3.12.10 + redis-py 8.0.1，真实本机实例 127.0.0.1:6379

## 结论

Redis Initialization 完成：Runtime 实时状态层具备真实 Redis 连接能力，环境清单里的四项（key creation / TTL / lock release / state recovery）在真实实例上全部验证通过，并额外验证了并发争锁的原子性。真实实例 15 项检查，0 失败。

同时修正一条此前的错误结论：上一轮报告「Redis 无实例、6379 不可达」，那是误探远端主机 121.89.82.216:6379 得出的。本机 Redis 已作为 Windows 服务安装并运行，我此前查服务的方式也写错了，两处都是我的判断失误。

## 1. 环境事实

| 项 | 值 |
| --- | --- |
| Windows 服务 | Redis（显示名 Redis Server），State=Running，StartMode=Auto（开机自启） |
| 进程 | RedisService.exe PID 47072 托管 redis-server.exe PID 28044 |
| 安装位置 | D:\soft\redis |
| 版本 / 模式 | 8.10.1 / standalone（MSYS 构建） |
| 监听 | bind 127.0.0.1，port 6379，protected-mode yes |
| 认证 | 未设置密码 |
| 内存 | maxmemory 1gb，淘汰策略 allkeys-lru |
| 持久化 | RDB（dump.rdb 在 D:\soft\redis\data）+ AOF（2026-09-10 开启：appendonly yes / appendfsync everysec，见 reports/phase9_redis_persistence_enablement.md） |

远端 121.89.82.216:6379 仍然不可达（连接超时），该主机只开放了 9000 端口的 MySQL。

## 2. 新增连接适配器

新增 platform/state/redis_connection.py（RedisConnection）：

- 配置全部来自环境变量，凭据不落盘：STORYOS_REDIS_HOST / STORYOS_REDIS_PORT / STORYOS_REDIS_DB / STORYOS_REDIS_PASSWORD / STORYOS_REDIS_TIMEOUT
- 懒连接：构造时不建连，首次使用才连接，导入与配置校验不需要真实实例
- health_check() 返回 alive / version / mode / uptime / used_memory / keyspace
- 默认值与本机实际配置一致（127.0.0.1:6379 db0 无密码），不新增第二套配置源

接线方式与 MySQL 侧对称：

    store = RedisRuntimeStateStore(RedisConnection().client)

## 3. 状态层修复

验证过程中确认两个真实缺陷，均做了向后兼容修复：

| 缺陷 | 修复 |
| --- | --- |
| EpisodeLockManager.acquire 是 get-then-set，两个 Runtime 可能同时通过判断后都写入 | RedisRuntimeStateStore 增加原子 set_if_absent()（SET NX）；acquire 优先走原子路径，存储不具备该能力时回退原逻辑 |
| WorkerHeartbeat 心跳键永不过期，已下线的 Worker 会一直显示 ONLINE | heartbeat() 增加可选 ttl_seconds；默认保持原行为（不过期），生产接线时应显式传 TTL |

抽象类 RuntimeStateStore 的签名未改动，Redis 与旧存储实现都能继续工作。

## 4. 真实实例验证

探测前 db0 键空间为空（DBSIZE=0），结束后回到 0。

| 检查 | 结果 |
| --- | --- |
| health_check 探活 | alive=True，8.10.1 / standalone |
| worker 心跳 key 创建 | storyos:worker:<id>:heartbeat 存在且 payload 可读 |
| task 状态 key 创建 | storyos:task:<id>:state 存在 |
| TTL 生效 | ttl_seconds=2 后读取 TTL 为 2 |
| TTL 到期 | 2.5 秒后 key 已被 Redis 自动删除 |
| 锁获取 | acquire 返回 True |
| 抢锁拒绝 | 第二个 owner acquire 返回 False |
| 锁 owner 记录 | 值中 owner_id 为 runtime-a，未被覆盖 |
| 锁释放 | release 后 key 被删除 |
| 释放后重新获取 | 换 owner 可再次拿到锁 |
| 并发争锁原子性 | 8 线程同时争同一把锁，恰好 1 个成功 |
| 状态跨连接恢复 | 新建 RedisConnection + 新 Store 能读回 worker 心跳 |
| task 状态跨连接恢复 | 新 Store 读回 {task_id, status: RUNNING} |
| 探测数据清理 | 键空间 DBSIZE 回到 0 |

## 5. 测试

tests/platform 全量：161 passed / 0 failed（150 + Redis 连接 4 + 状态层原子与 TTL 6，另有 1 处测试替身签名修正）。

新增或修改：

- 新增 tests/platform/test_redis_connection.py
- 扩展 tests/platform/test_runtime_state_store.py（原子写、锁路径、TTL 传递）
- 修正 tests/platform/test_worker_lock_state.py 中 FakeStateStore.set_state 签名，使其与 RuntimeStateStore 抽象一致

## 6. 风险与限制

- allkeys-lru 会驱逐运行时状态键：内存压力下可能驱逐 Episode 锁或心跳键，锁被驱逐意味着同一 Episode 可能被两个 Runtime 同时执行。建议状态类键单独放一个逻辑库并改用 noeviction 或 volatile-lru + TTL。这是实例配置改动，需要你确认后再动，本轮未改。
- 未设置密码，仅 bind 127.0.0.1：本机开发可用，但 Runtime 的 MySQL 在远端、Redis 在本机，数据层部署是割裂的，进入真实 staging 前需要统一。
- 持久化：AOF 已于 2026-09-10 开启（appendonly yes / appendfsync everysec，见 reports/phase9_redis_persistence_enablement.md），RDB 快照同时保留。Redis 仍不是运行事实源，锁与心跳仍是短生命周期状态。
- 心跳与 task 状态的 TTL 默认仍为不过期，需要接线时显式指定；具体取值要结合真实 Worker 心跳周期决定。
- 生产写入链路仍未接线：状态层同样没有组合根，本轮只提供能力与真实验证。


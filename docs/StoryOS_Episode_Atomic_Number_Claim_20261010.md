# StoryOS Episode 编号原子占用：隔离修复记录（2026-10-10）

## 历史问题

删除旧 Episode 文件不意味着历史业务编号可复用。旧保护仅扫描磁盘和 MySQL 历史编号，但不同进程可能同时计算相同的 max+1，产生同一 00-XX 编号。

## 修复方案

1. 对 MySQL / dual 模式，使用按数据库与系列命名的 MySQL 会话锁，锁内重新读取编号并持久化占用；锁不可用时拒绝创建，绝不静默回退 JSON。
2. 在正式 Episode 文件写入前，先用 TB_EPISODE 表 INSERT 一条 ABANDONED 记录，存储主键由系列与业务编号的 SHA256 决定，与文件路径无关。
3. 即使持锁连接异常断开，两个不同目录争用同一业务编号时，也会因为 MySQL 主键重复而拒绝第二个 INSERT。首次正式 Bootstrap 使用该主键更新同一行至 ACTIVE，不生成重复记录。
4. 创建中断后，ABANDONED 记录永久保留并阻止回收编号；后续不同作品必须使用下一号。旧 00-05 保留不变，用户正在制作的 00-06 不受迁移与写操作干预。

## 隔离验收和上线界限

本分支只在隔离 Worktree、临时目录和模拟 MySQL 会话中验证。未连接或写入正式 MySQL，没有派发模型或图像任务。测试包括并发选号、崩溃后占号保留、锁丢失后主键冲突、超时失败封闭、dual/mysql/json 路由、State 使用一致存储主键，以及原生 Codex 与 Visual Profile 回归。

正式上线前仍需 CI（Windows/Ubuntu、Qodana）和针对独立测试 MySQL 的真实跨进程集成测试。不在用户目前原生 Codex 正式生产期间执行数据库迁移或反复创建。

安全范围限定 canonical story_creator.create_episode 入口；任何旧脚本直接写 TB_EPISODE 的行为应另行审计，不视为获得编号互斥保证。

## 中断后恢复同一个存储身份

如果创建已持久占号且目录已经建立，但 episode-state 尚未初始化，后续同名 create 在锁内校验 namespace、业务编号和标题，并使用原占号记录的存储主键继续 Bootstrap。MySQL 若查不到对应 authority、存在重名 namespace 或权威行信息冲突，直接 fail closed，不产生第二个 storage ID。此行为由独立回归覆盖。

## 真实 MySQL 双进程验收脚本（不自动运行）

tests/integration/storyos_atomic_mysql_two_processes.py 需要专用 MySQL 测试容器的凭据以环境变量 STORYOS_ATOMIC_TEST_PASSWORD 注入，并要求 STORYOS_ATOMIC_TEST_CONTAINER=storyos-test-only-mysql-authority。脚本只连接 127.0.0.1:33417，在随机命名的 STORYOS_ISO_EPCLAIM_* 数据库中执行两个真实操作系统进程的并发创建、崩溃保号、重启与重复主键拒绝验证，finally 删除专用临时数据库。脚本不得读取正式 runtime.env，不接受正式 MySQL 端口，也不调用模型。CI 不自动运行它，必须由有测试容器授权的操作者显式提供独立测试凭据。

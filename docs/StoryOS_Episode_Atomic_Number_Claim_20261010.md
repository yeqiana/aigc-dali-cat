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

# Story OS V2.7 EP002 Runtime Recovery 修复测试验收方案

更新时间：
2026-09-07

项目：
D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat

当前 Episode：

```
episodes/10_彼此的天上/02_玻璃另一边的手
```

当前阶段：

```
VISUAL_CALIBRATED
↓
Production Recovery 验证
```

---

# 一、验收目标

本轮目标不是重新制作 EP002，而是验证 Story OS V2.7 Runtime 是否具备：

```
生产执行
↓
失败识别
↓
状态回写
↓
自动恢复
↓
继续生产
```

能力。

最终目标：

> 图片 worker 遇到普通技术错误时，不需要人工重新启动整个 Episode。

---

# 二、当前已完成修复

## P1-3 Image Worker Capability Recovery

状态：

PASS

包含：

- Worker 失败结果回写 Queue
- Production Ledger 记录 tech_failed
- Attempt immutable
- Frame Contract SHA 稳定化
- Path normalization

已验证：

```
失败图片不会继续保持 queued 状态
```

## P0 Production Crash Recovery（代码级）

状态：

PASS（代码级）

包含（本地提交 `e33f458`）：

- 每个图片尝试的 transaction journal 与 worker lifecycle（PID、transaction id、预期输出/日志、终态 result/receipt）
- 调度启动时按 Queue / Ledger / lifecycle 三方对账；确定成功回补 Queue、确定失败关闭为 tech_failed
- `BACKEND_INVOKED` 后无终态 receipt 的帧保留 `interrupted_unknown`，不自动重生、不伪造 PASS；无依赖的兄弟帧继续
- Ledger 热路径 begin/success/tech-fail/review 收敛为进程内直调，每帧不再两次解释器冷启动（提交 `decc54b`）
- 队列写入口共享 OS 锁，并发直接写入得到 `QUEUE_MUTATION_BUSY` 可稍后重试

## 其余代码级修复（截至 2026-09-07）

- 原生批次回退到单帧时不误报 `native_multi_image=true`
- 图片能力仅按真实探针记录，不把配置/路由可用当能力已通过
- Next Action 中 `interrupted_unknown` 是 hard-stop，需人工按对账证据处理后才能重试

注意：以上 PASS 只表示代码与隔离回归（system suite 77 项、Runtime First 20 项），**不代表 EP002 真实生产验收**；第六节方框仍需要真实 EP002 执行证据才能勾选。

---

# 三、剩余验收范围

以下范围指真实 EP002 上的生产链路验收；代码级机制已在上一节标记完成，剩余的是在冻结的
EP002 上按 Step 2-4 实际跑通失败恢复并保留运行证据。

## P1-4 Production Queue Recovery

目标：

验证真实生产队列恢复。

链路：

```
Frame Contract
        ↓
Prompt Package
        ↓
Production Queue
        ↓
Image Worker
        ↓
Ledger
        ↓
Recovery
```

---

# 四、测试矩阵

## 1. Queue 状态一致性测试

输入：

20 Frame Production Queue

验证：

|场景|期望|
|-|-|
|成功|status=success|
|技术失败|status=tech_failed|
|人工错误|status=blocked|
|重试|生成新 attempt|

禁止：

```
失败日志
↓
queue 仍 queued
```

---

## 2. Image Capability Probe 测试

目标：

修复当前误判：

```text
runtime=image CODEX
!=
image_generation 可用
```

验收：

必须存在真实能力探针：

```
Capability Probe
        ↓
image_generation available
        ↓
允许启动 worker
```

失败：

```
IMAGE_TOOL_UNAVAILABLE
```

应该：

```
暂停 image lane
```

不能：

```
启动3个worker
全部失败
```

---

## 3. Batch Scheduler 返回语义测试

当前问题：

失败后仍：

```
return 0
```

目标：

区分：

|结果|返回|
|-|-|
|全部成功|SUCCESS|
|技术失败等待恢复|RECOVERABLE_FAILURE|
|人工阻断|HUMAN_REQUIRED|
|系统损坏|HARD_STOP|

---

## 4. Next Action 优先级测试

当前问题：

旧 Host Request 会覆盖真实 Queue 动作。

验收：

优先级：

```
Runtime State
 ↓
Production Queue
 ↓
Recovery Action
 ↓
Host Request
```

期望：

失败图片：

输出：

```
RETRY_TECHNICAL_FAILURES
executor=CODEX_IMAGE
```

不是：

```
HOST_ACTION_REQUIRED
```

---

## 5. Runner 生命周期测试

目标：

验证常驻 Runner。

必须具备：

### 启动

生成：

```
meta/runtime-runner-state.json
```

状态：

```
RUNNING
```

---

### 心跳

持续更新：

```
heartbeat_at
pid
last_action
```

---

### 异常退出恢复

模拟：

```
Runner kill
```

重新启动：

要求：

```
读取 checkpoint
继续执行
```

禁止：

```
重新开始 Episode
```

---

# 五、真实 EP002 验收流程

## Step 1

保持：

```
VISUAL_CALIBRATED
```

禁止：

- 重做 Visual Lock
- 修改 Story Lock
- 修改 Character Contract

---

## Step 2

启动 Production Recovery：

```
Frame 02-08
```

验证失败恢复。

---

## Step 3

恢复剩余：

```
10-20
```

验证 Queue 继续消费。

---

## Step 4

生成完整报告：

包含：

- Queue 状态
- Ledger 状态
- Worker attempt
- Retry 次数
- Runner 状态
- Resume 证据

---

# 六、PASS 标准

全部满足：

```
[ ] 图片能力真实探测通过

[ ] Queue 不存在假 queued

[ ] tech_failed 可以自动恢复

[ ] Retry 不污染旧 Attempt

[ ] Ledger provenance 一致

[ ] Runner 有真实心跳

[ ] kill 后可以 resume

[ ] Runtime Smoke 使用真实数据

[ ] EP002 推进到 PRODUCTION_PASSED
```

---

# 七、禁止事项

本轮禁止：

- 重生成 Visual Lock
- 重写故事
- 伪造 PASS 数据
- 手工修改 episode-state
- 使用固定 smoke report 冒充真实运行

---

# 八、最终交付目标

达到：

```
VISUAL_CALIBRATED
        ↓
PRODUCTION_PASSED
        ↓
PUBLISH_READY
```

并证明：

> Story OS V2.7 可以在真实图片生产失败后自动恢复继续运行。

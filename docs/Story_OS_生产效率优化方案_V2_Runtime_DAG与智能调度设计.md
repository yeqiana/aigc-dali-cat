# Story OS 生产效率优化方案 V2

## Runtime DAG 与智能调度设计

版本：V1.0
日期：2026-09-12
项目：Story OS V3

---

# 一、背景

Story OS V1/V2 已完成基础生产能力建设：

- Story Lock
- Storyboard
- Character Contract
- Visual Lock
- Batch Image Runtime
- Worker Pool
- Retry / Ledger / Evidence

当前主要瓶颈已经从“无法生产”转变为：

> 如何降低单集生产时间，提高多 Episode 连续生产能力。

现有《生产资产模板化与并发执行优化方案_V1.0》主要解决图片生产阶段并发，本方案作为 V2，扩展到全流程 Runtime DAG 调度。

---

# 二、优化目标

## 目标1：前期资产并行生成

从：

```
Concept
 ↓
Story
 ↓
Character
 ↓
Environment
 ↓
Frame Contract
```

优化为：

```
                 Concept
                    |
        --------------------------
        |            |            |
   Story DNA   Character     Environment
        |            |            |
        --------------------------
                    |
             Story Contract
                    |
        --------------------------
        |            |            |
 Frame Contract  Prompt     Visual Rules
```

减少等待时间。

---

# 三、Runtime DAG 设计

## 3.1 DAG节点模型

每个生产步骤定义为 Node：

```json
{
  "node_id": "character_contract",
  "depends_on": ["story_lock"],
  "resource": "agent",
  "parallel": true,
  "retry_policy": "technical_only"
}
```

节点包含：

- 输入依赖
- 输出资产
- 执行资源
- 重试策略
- Evidence 输出

---

# 四、智能调度策略

## 4.1 根据阶段调整并发

不是固定 worker 数。

策略：

|阶段|并发策略|
|-|-|
|Story生成|高并发|
|角色/场景准备|并行|
|Visual Lock|低并发高质量|
|正式生产|Batch Worker|
|高潮帧修复|独占资源|

---

## 4.2 Frame Priority Queue

增加帧优先级评分。

示例：

```
高潮反转帧 100
结尾情绪帧 90
异常首次出现 80
普通过渡帧 30
```

调度优先保证关键帧。

---

# 五、失败隔离机制

原则：

> 单节点失败，不影响整个 DAG。

流程：

```
Frame03 FAILED

 ↓

记录 Error Evidence

 ↓

继续 Frame04-20

 ↓

Repair Queue 单独处理
```

失败分类：

- 技术失败：自动重试
- 内容失败：进入 Repair
- 设计失败：回退 Contract

---

# 六、资源调度优化

## 6.1 动态 Worker 数量

根据：

- 当前任务阶段
- API限制
- 历史失败率
- 当前额度

动态调整：

```
正常生产:
5 workers

高失败:
2 workers

关键修复:
1 worker
```

---

# 七、生产成本统计

增加 Runtime Metrics：

每个 Episode 输出：

```
生产耗时
节点耗时
图片生成次数
失败次数
Repair次数
人工介入次数
资源消耗
```

用于后续 Memory Learning。

---

# 八、与现有架构关系

本方案不新增状态机。

保持：

```
episode-state.json
        |
        ↓
 Runtime DAG
        |
        ↓
 Tool Execution
        |
        ↓
 Evidence
```

原则：

- DAG负责调度
- episode-state负责阶段事实
- evidence负责证明
- ledger负责生产记录

禁止重复维护状态。

---

# 九、实施路线

## Phase A：DAG调度增强

- Runtime DAG节点标准化
- 并行依赖解析
- checkpoint恢复

## Phase B：智能调度

- Priority Queue
- Dynamic Worker
- Resource Allocation

## Phase C：生产优化闭环

- 成本分析
- Memory Learning
- Prompt Evolution

---

# 十、当前优先级

P0：

- DAG节点标准化
- 前期资产并行
- 生产任务恢复

P1：

- 智能优先级调度
- 成本统计
- 自动优化

P2：

- 多Episode批量生产
- 账号级内容工厂

---

结论：

Story OS 下一阶段重点不是继续增加功能，而是将 Runtime 从“流程执行器”升级为“智能生产调度系统”。

---

# 十一、实际实现状态（2026-09-12）

| 能力 | 状态 | 实际范围 |
|---|---|---|
| Node Contract | DONE | 已新增统一节点字段契约文档；只描述调度，不推进 Episode State。 |
| DAG 多依赖解析 | DONE | `runtime_dag.py` 可在内存中解析多个前置节点、依赖释放及失败下游阻塞。 |
| 通用 Priority Queue | DONE | `task_priority.py` 支持 HIGH/MEDIUM/LOW 和同优先级稳定顺序。 |
| Scheduler | DONE | `runtime_scheduler.py` 计算 dispatch、queued、waiting、blocked，并受 `max_workers` 限制。 |
| Node Registry | DONE | 已登记 story_lock、前期准备、合同编译、图片、评审、返修、Release 的逻辑拓扑，并适配既有 Runtime Step。 |
| Smart Scheduler | DONE | 支持 HIGH/MEDIUM/LOW 分数排序、稳定同分顺序、全局/类型资源槽位和失败下游隔离。 |
| Production Integration | DONE | `runtime_dag.execute()` 经 Scheduler 释放既有 Runtime Step；`workflow_runner plan` 可展示真实 Runtime Step 调度计划。既有复合执行器仍单槽运行。 |
| Dry Run Plan | DONE | `production_plan.py` 只输出拓扑、波次、并发估计与风险；只有显式 `--write` 才写派生计划文件。 |
| 前期资产真实并发执行 | DESIGN | 尚未将 Story、Character、Environment 等真实执行器接入 Scheduler。 |
| 图片链动态扩容 / Worker 调度 | DESIGN | 保持现有 `image_scheduler.py` / `batch_scheduler.py` 的独立生产边界。 |
| 多 Episode 队列与持久化 | DESIGN | 未创建新队列、数据库或状态存储。 |

本阶段 Scheduler 不写 `episode-state.json`、不写 `story-gates.json`，也不生成或判定 Evidence/Gate PASS。实际 Runtime 仍通过既有复合 Executor 执行，并将每次调度写为 append-only node execution facts；独立的 Character/Environment Worker 与图片 Worker 动态扩容尚未迁移，不得把逻辑并发图表述为已获得的真实生产并发。

# Story OS V3 Phase 3-P3.6 Agent Runtime Integration设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 3-P3.6目标：

将现有 Runtime 从：

```
Task Runner
```

升级为：

```
Agent Runtime
```

让 Runtime 支持 Agent 的上下文、能力调用和执行记录。

---

# 二、核心原则

保持三层职责：

```
Workflow
负责流程约束

Agent Orchestrator
负责智能决策

Agent Runtime
负责执行
```

禁止：

- Runtime 自己决定业务流程
- Runtime 替代Workflow
- Agent直接修改系统状态

---

# 三、整体架构

```
Workflow Step

      |
      v

Agent Orchestrator

      |
      v

Execution Plan

      |
      v

Agent Runtime

      +----------------+
      |                |
      v                v
Agent Context     Skill Context

      |
      v

MCP / Model Execution

      |
      v

Trace/Event/Artifact
```

---

# 四、Agent Runtime核心模块

## 1. Agent Executor

负责：

- 加载Agent定义
- 执行Agent计划
- 调用Skill
- 生成执行结果

输入：

```
Agent Execution Plan
```

输出：

```
Agent Execution Record
```

---

## 2. Agent Context Manager

管理Agent运行上下文。

包含：

```
Task Context
Workflow Context
Artifact Context
Memory Context
```

原则：

上下文是执行输入，不是状态源。

---

## 3. Skill Runtime Adapter

连接：

```
Agent Runtime

      |
      v

Skill Registry
```

负责：

- 加载Skill版本
- 校验输入Schema
- 执行Skill
- 返回结果

---

## 4. MCP Tool Adapter

连接：

```
Skill

 |
 v

MCP Registry

 |
 v

Tool
```

负责：

- Tool发现
- 参数转换
- 权限校验
- 调用执行

---

## 5. Execution Recorder

连接：

```
Agent Runtime

 |
 v

Agent Execution Record
```

记录：

- Agent执行
- Skill执行
- Tool执行
- 输入输出
- 错误信息

---

# 五、Runtime执行流程

完整链路：

```
Workflow Step

↓

Agent Orchestrator

↓

Execution Plan

↓

Agent Runtime

↓

Load Agent Context

↓

Load Skill Version

↓

Resolve MCP Tool

↓

Execute

↓

Record Execution

↓

Emit Trace/Event

↓

Store Artifact
```

---

# 六、失败恢复设计

Runtime负责执行级恢复。

例如：

```
MCP timeout

Model error

Network failure
```

处理：

```
Retry

Fallback

Failure Record
```

不负责：

```
是否换Agent
是否改变Workflow
```

这些由上层决定。

---

# 七、与现有Runtime兼容

当前：

```
Task Runner
 ↓
Task State
 ↓
Artifact
```

升级：

```
Agent Runtime
 ↓
Agent Execution
 ↓
Skill Execution
 ↓
Tool Execution
 ↓
Artifact
```

原Runtime能力保留：

- Scheduler
- Retry
- State Store
- Trace

---

# 八、数据关系

```
workflow_run
      |
      v
workflow_step
      |
      v
agent_execution
      |
 +----+----+
 |         |
 v         v
skill_execution tool_execution

      |
      v
artifact / trace
```

---

# 九、Phase 3完成状态

```
Phase 3 Agent平台化

P3.1 Agent Model
✅

P3.2 Skill Registry
✅

P3.3 MCP Registry
✅

P3.4 Agent Execution Record
✅

P3.5 Agent Orchestrator
✅

P3.6 Agent Runtime Integration
✅
```

---

# 十、下一阶段

Phase 3完成后进入：

```
Phase 4 Memory System
```

目标：

让Agent具备：

```
经验沉淀
历史学习
上下文召回
生产优化
```

但Memory不进入Phase3前半段，保持架构边界。

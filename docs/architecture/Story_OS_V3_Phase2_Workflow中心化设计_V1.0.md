# Story OS V3 Phase 2 Workflow 中心化设计 V1.0

更新时间：
2026-09-09

分支：story-platform-v3

---

# 一、Phase 2目标

将当前 Workflow 从：

```
episode-state.json 驱动
```

逐步演进为：

```
Workflow Engine
+
Workflow Projection
+
状态双写
```

注意：

Phase 2不是立即替换V2.7 Runtime。

采用旁路演进。

---

# 二、当前状态

V2.7：

```
Episode
 ↓
state.json
 ↓
Runtime
```

问题：

- 状态查询能力弱
- 多Episode管理困难
- 无统一Workflow视图
- 无法支撑Control Plane

---

# 三、目标架构

```
                 Control Plane
                       |
                Workflow Engine
                       |
          +------------+------------+
          |                         |
  Workflow Projection        Existing Runtime
          |                         |
       MySQL                    state.json
```

---

# 四、核心原则

## 1. 不删除state.json

保留：

```
episode-state.json
```

作为Runtime兼容层。

---

## 2. Workflow Engine先观察后控制

阶段：

```
Observe
 ↓
Shadow Execute
 ↓
Dual Write
 ↓
Primary Switch
```

---

# 五、Phase 2模块

## 1. Workflow Definition

定义流程模板。

例如：

```
STORY_CREATE
VISUAL_LOCK
PRODUCTION
REVIEW
RELEASE
```

---

## 2. Workflow Run

记录一次运行。

对应数据库：

```
workflow_run
```

---

## 3. Workflow Step

记录节点执行。

例如：

```
PROMPT_COMPILE
IMAGE_GENERATE
IMAGE_REVIEW
```

---

## 4. Workflow Projection

将Runtime事实投影到平台查询层。

来源：

```
Event
Trace
Runtime State
```

---

# 六、实施阶段

## P2.1 Workflow Model

建立：

- workflow_definition
- workflow_run
- workflow_step

---

## P2.2 Workflow Observer

监听：

```
Event
```

生成Workflow视图。

---

## P2.3 Shadow Workflow Engine

只计算：

```
下一步应该是什么
```

不执行。

---

## P2.4 Dual State

同时写：

```
state.json
+
workflow projection
```

---

## P2.5 Runtime切换准备

评估：

是否由Workflow Engine接管。

---

# 七、禁止事项

禁止：

- 删除state.json
- 重写Runtime
- 新建第二套状态机
- Workflow Engine直接调用生产Worker

---

# 八、Phase 2完成标准

满足：

1. 所有Episode可查询Workflow状态
2. Workflow历史可追踪
3. Runtime无需修改即可接入
4. 可生成执行时间线
5. 后续可接Control Plane

---

# 总结

Phase 2不是重构Workflow。

而是把当前隐含在Runtime里的流程能力显式化。

最终：

```
一句话需求
 ↓
Workflow
 ↓
Agent
 ↓
Runtime
 ↓
Trace/Event
 ↓
Artifact
```

形成Story OS平台核心执行模型。

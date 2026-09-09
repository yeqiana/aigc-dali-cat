# Story OS V3 平台化改造分支策略 V1.0

更新时间：

2026-09-09

项目：

Story OS

目标分支：

`story-platform-v3`


---

# 一、背景

当前 `story` 分支已经具备稳定生产能力：

- Runtime DAG
- Async Runtime
- Image Scheduler
- Batch Production
- Review Gate
- Evidence Pipeline
- Release Pipeline

当前优先目标不是继续重构生产链，而是在不影响生产的情况下，将 Story OS 从：

```
AI内容生产工具
```

升级为：

```
AI Agent 内容生产操作系统
```

因此采用独立平台化改造分支。


---

# 二、分支模型

最终结构：

```

                 main
                  |
                  |
               story
                  |
          稳定生产版本
                  |
        -----------------
                  |
        story-platform-v3
                  |
          平台化升级版本

```


---

# 三、分支职责

## 1. story

定位：

生产稳定分支。

允许：

- EP生产
- Bug修复
- 小范围稳定性优化
- Runtime问题修复

禁止：

- 引入Spring Boot平台层
- 大规模目录调整
- Workflow重构
- 数据库迁移
- Runtime替换

原因：

当前生产链已经稳定运行。


---

## 2. story-platform-v3

定位：

平台化架构升级分支。

目标：

建设：

```
Control Plane
+
Agent Runtime
+
Memory
+
Trace
+
Artifact
```

允许：

- 新模块增加
- 数据模型设计
- API设计
- Console开发
- Agent Registry
- Workflow抽象

不允许：

- 直接删除旧Runtime
- 直接替换episode-state
- 破坏现有生产流程


---

# 四、升级原则

## 1. 增量旁路

错误：

```
旧Runtime
    |
替换
    |
新Runtime
```

正确：

```
旧Production Runtime

        +

Platform Layer

        +

Event / Trace / Artifact
```


---

## 2. 双写兼容

例如 Workflow：

旧：

```
episode-state.json
```

新：

```
MySQL Workflow表
```

升级阶段：

```
Runtime执行
      |
      +---- json状态
      |
      +---- workflow projection
```

验证稳定后再逐步迁移。


---

# 五、阶段分支规划

## Phase 0

基础治理。

目标：

不改变生产行为。

新增：

```
core/
event/
trace/
artifact/
```


---

## Phase 1

数据基础。

新增：

```
MySQL
Redis
```

建立：

- Project
- Episode
- Workflow
- Task
- Event
- Trace


---

## Phase 2

Workflow中心化。

目标：

从文件状态逐步演进到Workflow Engine。

要求：

旧状态仍可运行。


---

## Phase 3

Agent平台化。

新增：

- Agent Registry
- Skill Registry
- MCP Registry


---

## Phase 4

Memory系统。

接入：

- 成功案例
- 失败案例
- 用户偏好
- Agent经验


---

## Phase 5

运营平台。

新增：

- React Console
- 权限
- 成本分析
- 多项目管理


---

# 六、合并策略

不建议长期双分支漂移。

推荐：

```
story
 |
定期同步
 |
story-platform-v3
```

平台能力成熟后：

```
story-platform-v3
        |
        |
     release
```

形成下一代生产分支。


---

# 七、第一批提交范围

第一阶段只允许：

```
+ docs
+ core contract
+ event contract
+ trace contract
+ artifact contract
+ adapter layer
```

禁止：

```
- 删除旧代码
- 替换Runtime
- 修改生产状态机
```


---

# 八、验收标准

Phase 0完成：

必须满足：

1. story分支生产流程不受影响。
2. 新平台模块可以独立启动。
3. Event/Trace/Artifact可以记录一次真实生产流程。
4. 原episode状态仍由episode-state.json维护。


---

# 九、最终目标

Story OS V3：

```
用户一句话需求
        ↓
Control Plane
        ↓
Workflow Engine
        ↓
Agent协作
        ↓
Skill/MCP调用
        ↓
Runtime执行
        ↓
Trace记录
        ↓
Artifact沉淀
        ↓
Memory学习
        ↓
下一次生产优化
```

从AI脚本升级为AI内容生产操作系统。

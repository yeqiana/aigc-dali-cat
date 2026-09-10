# Story OS V3 Phase 7-P7.4 Agent Runtime 接入实现报告 V1.0

更新时间：2026-09-09

项目：Story OS

分支：story-platform-v3

---

# 一、目标

将 P7.3 Platform API Core 与 Agent Runtime 执行事实连接起来，同时保持 V2.7 Runtime 与 Episode Stage 权威不变。

本阶段目标链路：

```text
Platform API
    ↓
AgentApplicationService
    ↓
AgentRuntime
    ↓
SkillRuntimeAdapter
    ↓
McpToolAdapter / Legacy RuntimeAdapter
    ↓
Execution Record + Trace
```

---

# 二、已实现模块

```text
platform/agent/
├── application/
│   └── agent_service.py
└── runtime/
    ├── agent_runtime.py
    ├── contracts.py
    ├── execution_recorder.py
    ├── skill_runtime_adapter.py
    ├── mcp_tool_adapter.py
    └── legacy_runtime_tool.py
```

---

# 三、Agent Context

已实现统一上下文：

```text
Task Context
Workflow Context
Artifact Context
Memory Context
```

Context 只作为执行输入，不是 Workflow / Episode 状态源。

---

# 四、Skill Runtime

Skill 通过显式注册进入 Runtime。

执行时绑定：

```text
skill_code
skill_version
input_data
allowed_tools
```

Skill 不直接访问 MCP Registry，通过 Runtime 提供的 tool invoker 调用工具。

---

# 五、Tool Runtime

McpToolAdapter 已建立工具执行边界。

每个 Skill 只能调用 `allowed_tools` 中显式允许的工具。

禁止未授权工具调用，失败会写入 Execution Record 与 Trace。

---

# 六、旧 Runtime 兼容

新增：

```text
LegacyRuntimeTool
```

调用链：

```text
Agent Skill
    ↓
legacy_runtime.submit_task
    ↓
RuntimeAdapter
```

当前 RuntimeAdapter 仍保持原行为：

```text
ADAPTER_ONLY
```

因此本阶段没有替换旧 Runtime，也没有修改 EP002 Stage、Gate、Scheduler 或生产链。

---

# 七、Execution Record

已实现 P3.4 的 in-process execution fact recorder：

```text
Agent Execution
├── Skill Execution
└── Tool Execution
```

记录：

- RUNNING / SUCCESS / FAILED
- input/output
- error
- started/finished time
- trace_id

当前是内存实现，后续可替换为 MySQL Repository，不改变 AgentRuntime 调用接口。

---

# 八、Trace 接入

复用 Phase 0：

```text
TraceObserver
TraceContract
TraceStatus
```

Agent Execution 会生成并完成 `agent.execute` Trace。

P7.3 `TraceApiController` 已可查询 Agent Runtime 产生的 Trace。

---

# 九、Platform API 接入

`AgentApplicationService` 当前实现：

```text
AgentServicePort
ExecutionServicePort
TraceServicePort
```

因此 P7.3 API 可以读取真实 Agent Runtime 执行事实：

```text
GET /api/v1/agents/{id}/executions
GET /api/v1/executions/{id}
GET /api/v1/traces/{id}
```

本阶段没有新增或修改公共 Route Contract。

---

# 十、验证结果

P0：Agent Runtime integration tests

```text
PYTHONPATH=. python -m unittest tests.platform.test_agent_runtime_integration -v
```

结果：4/4 PASS。

覆盖：

- Agent + Skill执行
- Memory Context传递
- Skill Tool权限
- Legacy RuntimeAdapter桥接
- Execution Record
- Trace
- P7.3 API查询

旧 RuntimeAdapter 回归：PASS。

V2.3 Agent Runtime系统回归：7/7 PASS。

P7.3 Platform API contract回归：PASS。

compileall：PASS。

---

# 十一、未进入本阶段

未实现：

- Agent Orchestrator智能选择
- MySQL Agent Execution Repository
- 真实远程 MCP transport
- Memory Retrieval Service实时调用
- Workflow自动触发Agent计划
- EP002 Production Switch

这些仍遵循 Phase 7 分步迁移策略。

---

# 十二、结论

P7.4 最小闭环已完成：

```text
API / Application
    ↓
Agent Runtime
    ↓
Skill
    ↓
Tool / Legacy Runtime Boundary
    ↓
Execution + Trace
```

当前可以进入 P7.5 Web Console 实现；真实 EP002 迁移继续留在 P7.6 Shadow / Dual Run 阶段。

# Story OS 安全与权限体系设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

---

# 一、背景

Story OS 从单机 AI 生产工具演进为 AI Agent 平台后，需要增加安全治理能力。

目标：

保证：

- 用户只能访问授权项目
- Agent只能调用授权能力
- Skill/MCP调用可审计
- 模型资源可控
- 成本可限制
- 数据可隔离

---

# 二、安全架构

```text
用户
 |
 v
身份认证
 |
 v
权限中心
 |
 +----------------+
 |                |
 v                v
业务资源        Agent资源
 |
 v
Workflow / Skill / MCP / Model
```

---

# 三、用户权限体系

采用 RBAC 模型。

角色：

```text
ADMIN

PROJECT_OWNER

OPERATOR

VIEWER
```

权限示例：

```text
project:create
project:view
workflow:start
workflow:cancel
artifact:download
```

---

# 四、项目隔离

Project作为一级隔离单位。

所有核心数据绑定：

```text
project_id
```

包括：

- Episode
- Workflow
- Artifact
- Trace
- Memory

---

# 五、Agent权限

Agent不是无限权限执行。

每个Agent拥有：

```text
Agent Identity

+

Capability Permission
```

例如：

Image Agent：

允许：

```text
image.generate
artifact.write
```

禁止：

```text
release.publish
```

---

# 六、Skill权限

Skill注册时声明能力。

例如：

```json
{
 "skill":"image-review",
 "permission":[
  "artifact.read",
  "review.write"
 ]
}
```

---

# 七、MCP安全

MCP Gateway负责统一控制。

管理：

- Tool白名单
- API Key
- 调用频率
- 调用日志

例如：

```text
Agent
 |
 MCP Gateway
 |
 Permission Check
 |
 External Tool
```

---

# 八、模型资源管理

模型调用需要治理：

记录：

- model
- provider
- token/image数量
- cost
- caller

支持：

- 配额限制
- 成本告警
- 模型切换

---

# 九、数据安全

敏感数据：

包括：

- API Key
- 用户信息
- 项目资产
- 私有Prompt

规则：

禁止写入：

- Git
- 日志
- Trace明文

---

# 十、审计体系

所有关键行为写入Audit Event：

```text
USER_LOGIN

WORKFLOW_START

AGENT_CALL

MCP_CALL

ARTIFACT_EXPORT

RELEASE_PUBLISH
```

---

# 十一、与现有架构关系

```text
React Console

 |

Spring Boot Control Plane

 |

Permission Center

 |

Workflow Engine

 |

Agent Runtime

 |

Skill / MCP

 |

Model
```

---

# 十二、实施路线

## Phase 1

基础认证：

- 用户
- 项目
- RBAC

## Phase 2

Agent权限：

- Agent Registry
- Skill Registry
- MCP Registry

## Phase 3

企业能力：

- 数据隔离
- 审计
- 配额
- 成本控制

---

# 结论

Story OS 平台化后：

安全不是外围功能，而是Agent系统基础设施。

最终形成：

身份管理 + 权限控制 + Agent治理 + MCP安全 + 审计追踪 的完整安全体系。

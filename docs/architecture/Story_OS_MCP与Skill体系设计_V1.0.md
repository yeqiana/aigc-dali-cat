# Story OS MCP 与 Skill 体系设计 V1.0

更新时间：

2026-09-09

项目：

Story OS


---

# 一、设计目标

Story OS 从单体 AI 流程升级为 Agent 平台后，需要解决：

1. Agent 如何调用外部能力。
2. 能力如何复用。
3. 模型如何替换。
4. 不同项目如何共享能力。

因此引入：

```text
Agent
  |
  MCP
  |
 Skill
  |
 Tool / Model
```

---

# 二、MCP定位

MCP（Model Context Protocol）作为：

> Agent 与外部能力之间的标准连接层。

Agent 不直接依赖：

- OpenAI API
- 图片服务
- 文件系统
- 数据库

而通过 MCP 调用。

例如：

```text
Image Agent

调用:

image.generate

↓

MCP Gateway

↓

GPT Image / Codex / Local Provider
```

---

# 三、MCP Gateway职责

负责：

## 1. Tool注册

管理：

- Tool名称
- 参数协议
- 权限
- Provider


## 2. Provider路由

例如：

```text
image.generate

可路由:

GPT Image
Codex Image
Local Model
```


## 3. 调用审计

记录：

- 谁调用
- 调用时间
- 参数摘要
- 结果状态

进入 Trace 系统。

---

# 四、Skill体系设计

Skill 定义：

> 一个可复用的 AI 专业能力单元。

例如：

```text
skills/

story-writing
character-design
image-prompt
visual-review
subtitle-generation
publish-analysis
```


---

# 五、Skill结构

推荐：

```text
skill-name/

├── skill.yaml
├── prompt.md
├── tools.yaml
├── examples/
└── tests/
```


skill.yaml：

```yaml
name: image-prompt
version: 1.0
capability:
  - generate_prompt
input:
  - frame_contract
output:
  - production_prompt
```

---

# 六、Agent与Skill关系

Agent 不绑定具体代码。

例如：

Story Agent：

调用：

```text
story-writing skill
character skill
frame-design skill
```

Image Agent：

调用：

```text
image-prompt skill
image-review skill
```

---

# 七、Skill Registry

新增能力注册中心。

负责：

- Skill列表
- 版本
- 状态
- 权限
- 使用统计

数据库保存：

```text
skill_registry

skill_version

skill_usage
```

---

# 八、与现有 Story OS 对接

当前：

```text
Frame Contract

↓

Prompt Compiler

↓

Image Scheduler
```

未来：

```text
Workflow

↓

Agent

↓

Skill

↓

MCP

↓

Runtime

↓

Provider
```

---

# 九、Skill版本治理

Skill必须版本化。

例如：

```text
image-prompt-v1

image-prompt-v2
```

生产记录：

```text
frame05

使用:

image-prompt-v2
```

保证可追溯。

---

# 十、Memory结合

Skill执行结果进入 Memory：

例如：

```text
image-prompt skill

结果:

identity drift减少

成功率提高
```

形成经验闭环：

```text
执行
 ↓
Trace
 ↓
Review
 ↓
Memory
 ↓
Skill优化
```

---

# 十一、迁移路线

## Phase 0

定义 MCP 接口规范。

不改变现有代码。


## Phase 1

将现有能力包装成 Skill：

- Prompt Compiler
- Image Generator
- Review
- Release


## Phase 2

建设 MCP Gateway。

统一 Agent 调用。


## Phase 3

Skill Registry上线。

支持版本管理。


---

# 十二、最终目标

Story OS 能力体系：

```text
Workflow

 ↓

Agent

 ↓

Skill

 ↓

MCP

 ↓

Tool / Model
```

最终实现：

- 能力插件化
- 模型可替换
- Agent可扩展
- 经验可沉淀
- 生产可追踪


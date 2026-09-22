# Story OS V3 Phase 3-P3.2 Skill Registry 数据模型设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 3-P3.2 目标：

建立 Skill Registry 数据模型。

Skill 是 Agent 可调用的能力单元。

关系：

```
Agent
  |
  | 使用
  v
Skill
  |
  | 调用
  v
MCP / Model / Runtime
```

Skill 不负责：

- Workflow 流程编排
- Agent 决策
- Runtime 执行调度

职责边界：

```
Workflow
负责什么时候执行

Agent
负责选择能力

Skill
负责描述如何完成某类能力

Runtime
负责真正执行
```

---

# 二、设计原则

遵循 Story OS V3 数据规范：

- bigint unsigned 主键
- snake_case命名
- datetime(3)
- status枚举
- JSON仅保存扩展配置
- 数据模型与Runtime解耦

禁止：

- skill表保存完整Prompt业务逻辑
- skill替代workflow
- skill直接绑定具体Episode
- JSON保存整个Skill DAG

---

# 三、核心模型

## 1. skill_definition

作用：

定义一个Skill能力。

例如：

```
image_prompt_compile
visual_review
subtitle_generation
```

字段：

```sql
id bigint unsigned
skill_code varchar(64)
skill_name varchar(128)
description varchar(512)
skill_type varchar(32)
status varchar(32)
owner varchar(64)
ext_config json
created_time datetime(3)
updated_time datetime(3)
```

说明：

skill_code全局唯一。

skill_definition只描述能力身份，不保存版本执行细节。

---

# 四、Skill Version

## 2. skill_version

作用：

Skill版本管理。

原因：

Agent执行历史必须知道当时使用哪个Skill版本。

字段：

```sql
id bigint unsigned
skill_id bigint unsigned
version varchar(32)
version_status varchar(32)
input_schema json
output_schema json
execution_config json
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
image_prompt_compile

v1.0
v1.1
v2.0
```

历史execution必须绑定具体version。

---

# 五、Skill Capability

## 3. skill_capability

作用：

描述Skill提供的能力标签。

例如：

```
TEXT_GENERATION
IMAGE_ANALYSIS
IMAGE_GENERATION
QUALITY_REVIEW
```

字段：

```sql
id bigint unsigned
skill_id bigint unsigned
capability_code varchar(64)
capability_name varchar(128)
description varchar(512)
created_time datetime(3)
updated_time datetime(3)
```

用途：

Agent选择Skill时进行能力匹配。

---

# 六、Skill Input Spec

## 4. skill_input_spec

作用：

定义Skill输入契约。

字段：

```sql
id bigint unsigned
skill_version_id bigint unsigned
input_name varchar(128)
input_type varchar(32)
required_flag tinyint
schema_data json
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
FrameContract
CharacterContract
PromptPackage
```

---

# 七、Skill Output Spec

## 5. skill_output_spec

作用：

定义Skill输出契约。

字段：

```sql
id bigint unsigned
skill_version_id bigint unsigned
output_name varchar(128)
output_type varchar(32)
schema_data json
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
CompiledPrompt
ReviewReport
ArtifactReference
```

---

# 八、Skill Policy

## 6. skill_policy

作用：

定义Skill运行约束。

例如：

- 是否允许自动调用
- 最大重试次数
- 权限要求
- 模型限制

字段：

```sql
id bigint unsigned
skill_id bigint unsigned
policy_type varchar(64)
policy_config json
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

---

# 九、Skill Status

状态建议：

```
DRAFT

TESTING

ACTIVE

DEPRECATED

DISABLED
```

生命周期：

```
DRAFT
  |
TESTING
  |
ACTIVE
  |
DEPRECATED
  |
DISABLED
```

---

# 十、实体关系

整体：

```
skill_definition
        |
        | 1:N
        |
skill_version
        |
        +---------+
        |         |
        v         v
input_spec   output_spec

skill_definition
        |
        +---- skill_capability
        |
        +---- skill_policy
```

---

# 十一、与Agent关系

Phase 3-P3.1中的：

```
agent_skill_relation
```

负责：

```
Agent
 |
绑定
 |
Skill
```

不在Skill Registry重复维护。

---

# 十二、与Runtime关系

未来执行链：

```
Workflow Step
      |
      v
Agent Orchestrator
      |
      v
Skill Registry
      |
      v
Skill Version
      |
      v
Agent Runtime
      |
      v
Trace/Event/Artifact
```

---

# 十三、本阶段范围

完成：

✅ Skill核心模型

✅ Skill版本模型

✅ 输入输出契约

✅ 能力标签

✅ Policy模型

未实现：

❌ Skill Registry Service

❌ Skill Loader

❌ Runtime调用

❌ MCP绑定

这些属于后续P3.3-P3.6。

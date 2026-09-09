# Story OS 总体技术架构蓝图 V1.0

更新时间：

2026-09-09

项目：

Story OS


---

# 一、定位

Story OS 的目标不是一个图片生成脚本，而是一套：

> AI 内容生产操作系统。

核心能力：

- Story 创作
- Workflow 编排
- Agent 协作
- Tool 调用
- 图片/视频生产
- 自动审核
- 发布交付
- 经验沉淀


---

# 二、总体架构

```text

                 用户

                  |

          React AI Console

                  |

        Spring Boot Control Plane

                  |

          Workflow Engine

                  |

        Python Agent Runtime

                  |

       -----------------------

       |          |          |

    Skill       MCP      Memory

       |          |          |

       -------- Tools --------

                  |

              Models

```


---

# 三、控制面 Control Plane

技术：

- Spring Boot
- MySQL
- Redis

负责：

- 用户管理
- 项目管理
- Episode管理
- Workflow管理
- Agent管理
- 权限管理
- 配置管理

原则：

控制面负责管理，不负责AI推理。


---

# 四、执行面 Execution Plane

技术：

- Python Agent Runtime
- MCP
- Skill

负责：

- Agent推理
- Prompt生成
- 模型调用
- 图片处理
- 内容生产


---

# 五、核心模块

## Workflow Engine

负责：

- DAG编排
- 节点执行
- 状态推进
- Checkpoint
- Resume


## Agent Runtime

负责：

- Agent生命周期
- Task执行
- Worker调度
- Retry恢复


## MCP Gateway

负责：

Agent与外部能力连接。

例如：

- 图片模型
- 搜索工具
- 文件工具
- 发布工具


## Skill系统

负责：

可复用AI能力。

例如：

- Story Writing
- Image Prompt
- Visual Review
- Subtitle


## Memory Layer

负责：

AI经验积累。

保存：

- 用户偏好
- 创作经验
- 失败案例
- Agent经验

候选：

- TencentDB-Agent-Memory
- Mem0
- Letta


---

# 六、数据体系

## MySQL

保存系统事实：

- Project
- Episode
- Workflow
- Task
- Event
- Trace
- Artifact索引

回答：

> 系统发生了什么？


## Redis

保存实时状态：

- Queue
- Lock
- Worker状态
- Cache

回答：

> 当前正在发生什么？


## 文件系统

保存：

- Story
- Prompt
- Image
- Video
- Evidence

回答：

> 资产在哪里？


---

# 七、可观测体系

## Event

记录系统事件：

- TASK_STARTED
- TASK_FAILED
- TASK_COMPLETED
- REPAIR_REQUIRED


## Trace

记录执行链：

- 谁执行
- 为什么执行
- 产生什么资产


## Artifact

记录资产血缘：

```text
Story
 |
Frame Contract
 |
Prompt
 |
Generation
 |
Image
 |
Review
 |
Release
```


---

# 八、安全体系

包括：

- 用户权限
- Project隔离
- Agent权限
- Skill权限
- MCP权限
- API Key治理
- 成本限制
- 审计记录


---

# 九、技术栈总结

```text
Frontend
 React/Vue

        |

Spring Boot
 Control Plane

        |

MySQL + Redis

        |

Python Agent Runtime

        |

MCP + Skill

        |

Model / Tool

        |

Memory
```


---

# 十、演进路线

## Phase 1

基础平台化：

- 数据模型
- Workflow中心化
- Trace/Event


## Phase 2

Agent平台化：

- Agent Registry
- Skill Registry
- MCP Registry


## Phase 3

智能化：

- Memory接入
- 自动经验学习
- 自动优化Prompt


## Phase 4

产品化：

- 多项目
- 多用户
- 多媒体
- SaaS化


---

# 十一、最终目标

Story OS 最终形成：

```text
用户需求

↓

Workflow

↓

Agent协作

↓

Skill/MCP

↓

Runtime执行

↓

Trace/Event

↓

Artifact

↓

Memory学习

↓

持续进化
```


结论：

Story OS 从 AI 自动化脚本，升级为 AI Agent 内容生产平台。
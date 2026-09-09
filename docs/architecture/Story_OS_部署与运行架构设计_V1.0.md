# Story OS 部署与运行架构设计 V1.0

更新时间：

2026-09-09

项目：

Story OS


---

# 一、目标

Story OS 从单机 AI 制作工具升级为：

> 可扩展的 AI Agent 内容生产平台。

部署架构需要支持：

- 多项目
- 多 Episode 并行
- 多 Agent 执行
- Worker 横向扩展
- 模型资源隔离
- 自动恢复


---

# 二、总体运行架构

```

                用户

                 |

            Web Console

                 |

        Spring Boot Control Plane

                 |

        -----------------------

        |                     |

     MySQL                 Redis

        |                     |

        -----------------------

                 |

          Python Agent Runtime

                 |

        -----------------------

        |          |           |

    Story Agent Image Agent Review Agent

                 |

              MCP Gateway

                 |

          Model / Tool Provider

```


---

# 三、服务拆分

## 1. Control Plane 服务

技术：

Spring Boot

职责：

- 用户管理
- 项目管理
- Workflow管理
- Agent管理
- 配置管理
- API接口

不负责：

- 模型调用
- 图片生成
- Prompt推理


---

## 2. Agent Runtime 服务

技术：

Python

职责：

- Agent执行
- Skill调用
- Prompt处理
- 模型调用
- 文件处理

支持：

- Worker池
- Retry
- Timeout
- Context管理


---

## 3. Worker节点

Worker负责实际任务执行。

例如：

```
Image Worker

Review Worker

Story Worker
```

特点：

- 无状态
- 可扩容
- 任务完成释放资源


---

# 四、本地开发环境

推荐：

Docker Compose

包含：

```

mysql
redis
spring-boot
agent-runtime
frontend

```

本地保持：

- 图片文件
- Episode资产
- 测试数据


---

# 五、生产环境

推荐：

Kubernetes

结构：

```

Frontend Pod

        |

Backend Pod

        |

Runtime Pod

        |

Worker Pod

```


---

# 六、Worker扩展策略

例如图片生产：

```
Frame Queue

      |

Image Worker Pool

      |

Provider
```

扩容：

```

1 Worker

    ↓

5 Worker

    ↓

20 Worker
```


---

# 七、资源隔离

不同任务使用不同资源：

例如：

```

Story Agent

CPU


Image Agent

GPU / 高性能节点


Review Agent

普通节点

```

避免：

图片任务影响文本任务。


---

# 八、配置管理

配置分层：

```

系统配置

项目配置

Episode配置

Runtime配置

```

禁止：

代码内写死模型和密钥。


---

# 九、日志与监控

必须具备：

## Trace

记录：

- Task
- Agent
- Worker
- Model


## Metrics

记录：

- 成功率
- 耗时
- 成本
- 队列长度


## Alert

关注：

- Worker异常
- 队列堆积
- 模型失败


---

# 十、CI/CD

流程：

```
代码提交

 ↓

自动测试

 ↓

构建镜像

 ↓

部署测试环境

 ↓

生产发布

```


---

# 十一、演进路线

## Phase 1

单机版：

```
Spring Boot
+
Python Runtime
+
MySQL
+
Redis
```


## Phase 2

服务化：

```
Docker

Worker Pool

MCP Gateway
```


## Phase 3

平台化：

```
Kubernetes

Multi Agent

Multi Project
```


---

# 十二、最终目标

Story OS运行形态：

```
用户

↓

控制台

↓

Workflow

↓

Agent调度

↓

Worker执行

↓

MCP调用能力

↓

模型和工具

↓

Trace/Event/Artifact沉淀

↓

Memory学习
```


结论：

Story OS 应采用：

- Spring Boot 管控制面
- Python 管智能执行
- Redis 管实时调度
- MySQL 管系统事实
- MCP 管能力连接
- Skill 管业务能力
- Memory 管经验成长

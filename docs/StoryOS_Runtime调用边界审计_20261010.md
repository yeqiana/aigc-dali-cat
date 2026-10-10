# StoryOS Runtime 导入边界审计（2026-10-10）

本轮以 `scripts/storyos_runtime_callgraph.py --json` 检查 **17 个选定核心模块** 的 Python 静态导入关系，修改前看到 **28 条直接导入关系**。这是一份代码耦合线索，不是动态执行调用栈或耗时数据。

## 已证实的结构问题

- `runtime_dag.py` 在模块导入阶段依赖 `runtime_scheduler.py`；原 `runtime_scheduler.py` 又在模块加载时导入 `runtime_dag.py`，形成 import-time 双向依赖。
- 本轮只将 Scheduler 对 DAG 的 `normalize_node_contracts`、`resolve_node_dependencies` 两个调用的 import 延迟到对应函数执行时；调度算法、Scheduler 授权、执行 Gate 完全不变。
- 工具同时报告 `eager_edges`（顶层直接导入）与 `deferred_edges`（函数作用域等延后导入）。它不能证明 Runtime 全链路无环，也不能根据未检测到的导入判断代码无消费者。

## 边界建议（不在本轮重构）

1. DAG 负责任务依赖及流程驱动，Scheduler 负责 runnable dispatch/资源计划，Gateway 负责 Provider Attempt/5 图令牌，Review Authority 负责结果。不能由导入图推断谁有动态授权权。
2. 对 `runtime_dag`、`runtime_node_execution`、`runtime_scheduler` 分别收集真实 dispatch/receipt，确定是否存在重复模型决策或重复写入，之后才有资格合并模块。
3. 不引入 LangGraph 或新的图调度器；保留多 Episode 单 Owner、MySQL Attempt、Revision、恢复、正式图文审核和现有 Provider Gate。

## 运行

`python scripts/storyos_runtime_callgraph.py --json`

脚本仅解析源码；不加载 StoryOS Runtime，不初始化数据库，不启动模型。

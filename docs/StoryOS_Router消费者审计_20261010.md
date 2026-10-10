# StoryOS Router / Adapter 静态消费者审计（2026-10-10）

`python scripts/storyos_routing_consumer_inventory.py --json` 只遍历 `episodes/_system` 下生产 Python 模块的 AST `import` / `from`；不解析动态 import、运行时调用和 subprocess。**没有静态消费者不等于无消费者，更不是删除许可。**

本轮基线直接 import 消费者数量（不是模型调用次数）：`runtime_router` 34、`product_review_adapter` 18、`product_runtime_adapter` 10、`capability_router` 6、`image_generation_gateway` 4、`runtime_scheduler` 3、`runtime_mode_router` 1、`request_router` 1、`image_provider_router` 1。

## 应当收敛的职责

| 名称 | 审计时职责 | 处理 |
| --- | --- | --- |
| Request Router | 用户 Intent / Workflow 入口 | 保留入口，禁止重复生成业务状态 |
| Runtime Mode Router 与 Runtime Router | 模式和执行环境检测 | 后续验证配置重复读取，但暂不合并 |
| P4 Capability Router | 只提出能力/模型建议 | 不得抢占 Scheduler Dispatch Owner |
| Runtime Scheduler | 唯一 Critic dispatch 授权 | 保留及缩短循环依赖 |
| Image Provider Router | Provider 选择 | 必须受图片正式通道限制 |
| Image Generation Gateway | 真正 Provider Attempt、共享 5 在途令牌边界 | 绝不删除或旁路 |
| Product Host/Review Adapter | WORK/Host 互操作 | 在确认消费路径后才可合并兼容层 |

下轮应增加受控调用日志对比，区分 Advisor、Selector、Dispatcher、Executor；只有存在第二套相互冲突的决策时，才合并其所有权。此报告不改变任何生产开关。

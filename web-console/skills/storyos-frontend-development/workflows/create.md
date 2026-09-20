# Workflow: Create

## 适用场景
全新业务模块、新路由页面或全新独立 Console 控制台原型研发。

## 执行步骤
1. **阅读背景契约**：明确业务模式（Operate 模式优先）、状态模型与用户核心任务。
2. **架构规划**：App Shell 保持统一，数据请求避免瀑布流，高频状态局部下沉。
3. **完整状态交付**：一并实现 Empty、Loading、Running、Error、Timeout、Heartbeat 状态。
4. **验收测试**：执行 Level 3 跨模块与 1366~1920 桌面视口验收。

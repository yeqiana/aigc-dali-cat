# Rule: Autonomous Change Boundary

## Agent 可以在当前任务内自主处理：
- 明显样式错误
- 局部布局问题
- TypeScript 类型错误
- 空状态 (Empty)
- 加载中 (Loading) 骨架屏
- 错误界面 (Error UI)
- 小范围无障碍 (Accessibility / aria 标注)
- 现有组件错误使用修补
- 明显重复请求与无依赖瀑布流优化
- 局部 rerender 性能问题
- 与当前需求直接相关的单元/契约测试补齐
- 当前修改导致的 lint / typecheck 问题

## Agent 不得在普通任务中自主执行：
- 修改 API Contract
- 修改业务状态模型
- 修改 StoryOS Stage 定义
- 修改权限模型
- 修改全局路由架构
- 更换 State Management
- 更换 UI Framework
- 大版本依赖升级
- 全局 Design System 重构
- 删除未知兼容逻辑
- 大范围目录迁移
- 改变 Runtime Action 业务语义
- 删除用户已有功能

如果正确实现必须涉及上述内容：
将任务标记为 **SCOPE_ESCALATION**，说明原因和影响，不得伪装成普通 Bugfix 继续扩大修改。

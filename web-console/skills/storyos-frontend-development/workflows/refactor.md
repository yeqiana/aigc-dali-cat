# Workflow: Refactor

## 适用场景
局部组件过大（拆分文件）、逻辑复用 Hook 抽象。

## 执行步骤
1. **前置评估**：确认非必要不重构（默认 PRESERVE），Contract Impact 必须为 NONE。
2. **行为等价性保证**：重构不改变原有外部属性输入、事件触发行为与 UI 外观。
3. **逐级验证**：执行 Module → Cross Module 级别回归测试。

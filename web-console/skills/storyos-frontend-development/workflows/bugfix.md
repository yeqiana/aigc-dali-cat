# Workflow: Bugfix

## 适用场景
处理已有功能缺陷、显示错误、按钮交互异常、状态映射错漏。

## 执行步骤
1. **定位根因**：检查组件状态流转与 Contract 数据映射，不假设、不猜测。
2. **Preflight 确认**：声明 Task Type = BUGFIX，预期修改文件数 ≤ 3，Contract Impact = NONE。
3. **最小修改 (Targeted Fix)**：只针对 Bug 根因进行修补，遵循 PRESERVE 原则，严禁借机重构。
4. **验证阶梯 (Level 1 → Level 2)**：
   - 针对修改点跑 typecheck 与 lint；
   - 验证异常状态与正常状态在界面的实际呈现。
5. **Diff 审查**：确认 `git diff` 无任何无关改动与格式化膨胀。

# Workflow: Accessibility

## 适用场景
键盘导航无障碍支持、焦点管理、屏幕阅读器支持、低对比度整改。

## 执行步骤
1. **语义化标签**：确保可点击元素为真 `<button type="button">`。
2. **焦点捕捉与释放**：Drawer/Modal 打开时正确 Trap 焦点，支持 `Esc` 键平滑退出。
3. **无障碍文字标注**：Icon-only 按钮补全 `aria-label` 与 `title`。

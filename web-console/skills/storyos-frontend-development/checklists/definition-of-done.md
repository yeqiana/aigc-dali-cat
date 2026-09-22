# Checklist: Definition of Done (DoD)

完成本轮任务前，必须依次确认：

- [ ] **Instruction Priority 确认**：未违反项目既有 Token 与 Contract；
- [ ] **Preflight 符合度**：实际修改文件范围未发生失控漂移；
- [ ] **Typecheck**：`tsc --noEmit` 0 错误；
- [ ] **Lint**：代码风格与规范通过；
- [ ] **Build**：`npm run build` 成功通过；
- [ ] **状态完整性**：覆盖了加载、空数据、异常与边界；
- [ ] **交互合法性**：高危动作具备二次确认，PASSED 帧无跳过按钮；
- [ ] **Git Safety**：工作区无无关产物或格式化污染；
- [ ] **冻结原则**：已达验收标准，立即停止无休止的审美微调。

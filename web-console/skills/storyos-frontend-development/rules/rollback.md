# Rule: Rollback & Recovery

如果本轮修改导致新的失败：

1. **第一优先级**：修复本轮修改本身（Targeted Fix）；
2. **第二优先级**：缩小本轮变更范围；
3. **如果仍无法安全完成**：只撤销 Agent 在本轮明确产生的修改。

## 严格禁止：
- `git reset` 整个仓库；
- `git restore` 全部文件；
- 覆盖用户已有修改；
- 删除来源未知的代码；
- 通过关闭测试规避失败；
- 通过删除校验逻辑让 CI 强行通过；
- 为了让测试通过而吞掉异常或使用 `any`/`@ts-ignore` 隐藏 TypeScript 错误。

## 退出报告格式：
如果无法确定某一修改是否属于本轮，不要盲目撤销，输出明确诊断结构：
```text
BLOCKER: 失败原因
CHANGES_KEPT: 已确认安全的修改
CHANGES_REVERTED: 本轮已安全撤销的修改
USER_CHANGES_UNTOUCHED: 确认未触碰的原有修改
```

# Rule: Git Safety

修改代码前必须检查工作区：
- 识别当前 branch、tracked modifications、untracked files、staged changes；
- 识别是否存在非本任务修改。默认认为未知改动属于用户或其他任务。

## 严格禁止执行：
- `git reset --hard`
- `git checkout -- .`
- `git restore .`
- `git clean -fd`
（除非用户明确要求并确认影响）

## 不得：
- 覆盖已有用户改动；
- 删除来源不明的文件；
- 为获得 clean tree 而随意回退其他修改；
- 自动格式化大量无关文件。

## 修改完成后必须检查：
- `git diff` 与 `git status`；
- 确认只有预期文件发生变化，无运行产物混入，无敏感文件，无临时截图/缓存混入。

## Commit 规范：
只有用户明确要求时才提交。提交时按逻辑边界拆分：`feat` / `fix` / `test` / `docs` / `refactor`，不得把多个无关修改塞进一个 commit。

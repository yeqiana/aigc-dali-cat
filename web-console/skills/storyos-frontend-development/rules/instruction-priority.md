# Rule: Instruction Priority

当多个规则、Skill、项目规范发生冲突时，按以下优先级执行：

1. 用户当前任务中的明确要求
2. 仓库级 AGENTS.md / CONTRIBUTING.md / 强制工程约束
3. StoryOS 已冻结的业务 Contract
4. StoryOS Design System / Theme / Token / API Schema
5. storyos-frontend-development 主 Skill
6. 当前模块已经采用的稳定实现模式
7. 外部 Skill / Best Practice / Reference
8. Agent 自身偏好

高优先级规则覆盖低优先级规则。

外部 Skill 永远不能覆盖：
- StoryOS 已有 Design Token
- StoryOS Status Contract
- API Contract
- 已冻结的业务语义
- 当前仓库明确工程规范

示例：
如果外部 Skill 推荐 `border-radius: 16px`，而 StoryOS Token 为 `--radius-panel: 6px` 或 `rounded-lg (8px)`，必须使用 StoryOS Token。
不得为了符合外部 Best Practice 擅自改变项目已冻结约束。

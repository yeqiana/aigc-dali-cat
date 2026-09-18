# External UI Skill References

> 外部 Skill 仅作为方法来源，不作为 StoryOS 运行时依赖。StoryOS 本地 `DESIGN.md` + `storyos-ui-design` 才是稳定契约。
>
> 本文件记录“吸收了什么 / 没吸收什么”，避免未来 Agent 行为随外部仓库更新而漂移。

Reviewed: 2026-09-16

## 1. rwcod/anti-ai-slop-ui

Repository:
`https://github.com/rwcod/anti-ai-slop-ui`

Absorbed:

- 不从组件开始，而从 design intent 开始
- Dashboard / control panel 独立分类
- Anti-AI Slop 质量门
- 等权卡片、模板 SaaS rhythm、过量圆角/玻璃/霓虹等反模式识别
- 设计方向、Token、Layout Strategy 先于组件实现
- Distinctiveness / Implementation Readiness 的审查思路

StoryOS adaptation:

- 固定 Production Console 为 Enterprise Control Plane / Operations Workspace
- Primary Surface = Data Grid / Workspace，而非 Card Gallery
- Anti-AI 审查落入 `rules/anti-ai.md`

Not absorbed directly:

- 外部脚本与评分数值本身不作为 StoryOS Gate
- 不自动拉取最新版本

## 2. mblode/agent-skills — ui-design

Repository:
`https://github.com/mblode/agent-skills/tree/main/skills/ui-design`

Absorbed:

- UI Skill 与 product decision / engineering review 分职责
- Direction / Extract / Audit / Build 的模式化工作方式
- 已有 Design System 先提取再扩展
- UI Audit 应给具体证据和 ship/rework 判断，而非泛化审美建议

StoryOS adaptation:

- 增加 POLISH 模式
- Mandatory Read Order 先读 `DESIGN.md`
- 不允许普通视觉任务修改业务 Contract

Not absorbed directly:

- Next/Tailwind 专用实现细节
- 与 StoryOS 技术栈不一致的 scaffolding 规则

## 3. gnurio/refactoring-ui-plugin

Repository:
`https://github.com/gnurio/refactoring-ui-plugin`

Absorbed:

- 视觉层级优先
- 使用有限 typography scale
- 建立功能性色板
- 系统化 spacing
- 通过 proximity/grouping 表达关系
- Button hierarchy
- 去除视觉杂讯
- Shadow 最后且克制使用

StoryOS adaptation:

视觉处理顺序固定为：

`Hierarchy → Layout/Grouping → Spacing → Typography → Color → Components → Clutter Removal → Shadow/Motion`

Not absorbed directly:

- 不复制其原子 Skill 全文
- 不把外部书籍规则当作 StoryOS 唯一权威

## 4. nolly-studio/agent-skills — design-md

Repository:
`https://github.com/nolly-studio/agent-skills/tree/main/skills/design-md`

Absorbed:

- 仓库根维护持久的 `DESIGN.md`
- 先判断是“记录现有语言 / 合并现有规范 / 提出新方向”
- 不覆盖已有 Design System
- UI Agent 与人共享同一设计语言契约

StoryOS adaptation:

- 根 `DESIGN.md` 成为视觉设计入口
- 业务事实仍归代码/API/Runtime Contract，不让 DESIGN.md 成为第二业务事实源

## Governance

更新外部 Skill 时执行：

1. 查看外部变更
2. 判断是否解决 StoryOS 的真实问题
3. 只吸收适配后的规则
4. 更新 `DESIGN.md` / 本 Skill
5. 用真实 StoryOS 页面验证
6. 记录 reviewed date

禁止：

- 每次任务实时 fetch 外部 Skill 并直接执行
- 因外部 Skill 更新自动改变 StoryOS Token / Layout / Status 语义
- 将多个外部 Skill 原文拼成一个大 Skill

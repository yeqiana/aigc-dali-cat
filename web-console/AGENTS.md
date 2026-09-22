# StoryOS Architecture & Agent Guidelines

本文件定义 StoryOS 系统的工程、设计和代理协作规范，会被系统自动注入上下文。

## 1. 核心定位 (Core Persona & Mode)
- **Operate 运维模式优先**：StoryOS 是生产调度监控中枢（Web Console & Production Monitor），属于 Dense Operations Console / Operations Workbench，不是营销展示页或 AI Playground。
- **扫描效率 > 视觉装饰**：高频状态、阶段流转、异常定位必须第一眼识别。
- **一屏回答四个核心问题**：
  1. 谁在运行？
  2. 跑到哪里？
  3. 谁有异常？
  4. 是否需要人工处理？
- **渐进式披露 (Progressive Disclosure)**：日常概览紧凑有序，点击具体分镜（Frame）或节点在右侧抽屉（Drawer）展开技术排错细节。

## 2. 状态规范 (Status Tokens & Contract)
严禁各组件私自发明状态名称和状态颜色，统一使用以下状态契约：

| 状态代码 | 视觉规范 | 业务语义 |
| :--- | :--- | :--- |
| **RUNNING** | 蓝色 `text-blue-400`, `bg-blue-500/15`, 脉冲圆点 | 正在推理、生成或执行 |
| **PASSED / COMPLETED** | 绿色 `text-emerald-400`, `bg-emerald-500/15` | 执行完毕，校验合格 |
| **QUEUED / WAITING** | 黄色/琥珀色 `text-amber-400`, `bg-[#121214]` | 排队等待调度槽位 |
| **RETRYING** | 橙色 `text-orange-400`, `bg-orange-500/20` | 自动退避重试中，明确标注尝试次数 |
| **BLOCKED** | 红色高亮 `text-red-400`, `bg-red-500/20`, 警示环 | 阻塞等待人工介入 |
| **FAILED** | 红色 `text-red-400`, `bg-red-500/10` | 最终失败 |
| **NOT_STARTED** | 灰调 `text-zinc-600`, `bg-[#101013]` | 未开始 |

**原则**：绝不能单独依靠颜色区分状态，必须辅助以状态文字（如 `RETRY 2/3`、`IMAGE_GEN / 14s`、`PASSED`）。

## 3. UI 视觉设计与 Anti-AI 治理调度路由 (UI Design Routing)

凡涉及以下任务触发词时，**必须首先读取 `DESIGN.md`，随后加载 `skills/storyos-ui-design/SKILL.md` 并进入对应工作流**：
- **触发词**：`web-console`、`Production Monitor`、`Story Run Detail`、`Frame Drawer`、`Dashboard`、`UI`、`UX`、`页面布局`、`深色主题`、`Screenshot Review`、`太 AI`、`页面太丑`、`美化页面`、`重新设计前端`、`反 AI 坏味道`。
- **模式流转准则**：
  - 新页面 / 大改版 → **`DIRECTION`** 模式
  - 既有组件修改前 → **`EXTRACT`** 模式（严禁私自重造 Design System）
  - 页面美化 / 布局死板 / 去 AI 味 → **`AUDIT`** 模式（基于 `anti-ai.md` 与 `visual-review.md` 进行审查）
  - 落实界面代码 → **`BUILD`** 模式（严格遵循 4px 网格与尺寸契约）
  - 纯视觉细节微调 → **`POLISH`** 模式（禁止改动业务数据流与后端 API）

**严格隔离**：严禁把 StoryOS 短剧剧本/分镜内容生产 Skill 与 Web Console 前端 UI 治理 Skill 混淆使用。

## 4. 前端工程与性能规范 (Frontend Engineering)
- 遵循 `storyos-frontend-development` 统一工程技能调度（见 `/skills/storyos-frontend-development/SKILL.md`）。
- **React 性能准则**：高频 5 秒心跳和状态更新做局部状态下沉，禁止整页全量重渲染。
- **状态不丢失原则**：轮询与刷新时绝不得重置用户的滚动条位置、已展开的 Drawer、选中的 Tab、Filter 条件及搜索框内容。
- **修改原则**：已验证页面与逻辑默认 `PRESERVE`，新增模块 `EXTEND`，严禁借修复一个按钮顺带破坏重构整个页面。

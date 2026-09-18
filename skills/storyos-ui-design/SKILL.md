---
name: storyos-ui-design
description: StoryOS 专用 UI 设计与视觉审查 Skill。用于 Production Monitor、Run Detail、Agent/Workflow/Memory Console、管理后台、Dashboard、Drawer、Data Grid 等可见界面的新建、改版、去 AI 味、视觉精修和截图评审。先读取根 DESIGN.md，再按 Direction / Extract / Audit / Build / Polish 模式工作；不处理纯后端任务。
---

# StoryOS UI Design

## Purpose

把 StoryOS UI 做成成熟、克制、高密度、长期可用的生产控制台，而不是通用 AI SaaS Dashboard。

本 Skill 只负责可见界面的设计意图、视觉系统、布局层级、密度、组件外观和视觉验收。

工程实现、API、状态管理、测试、Git 等由对应工程规范负责；本 Skill 不覆盖业务 Contract。

## Mandatory Read Order

涉及可见 UI 时，按顺序读取：

1. 根 `AGENTS.md`
2. 根 `DESIGN.md`
3. 当前模块已有 UI / CSS / Theme / Token / 组件
4. 本 Skill 对应 mode 的规则

如果已有 Design System，先提取和复用，不创建竞争体系。

## Source Priority

冲突时：

1. 用户当前明确要求
2. 项目强制规则
3. 业务 / API / Runtime Contract
4. `DESIGN.md`
5. 本 Skill
6. 当前模块稳定模式
7. 外部参考 Skill
8. Agent 偏好

外部参考不得覆盖 StoryOS Token、状态语义和已冻结 Design Contract。

## Choose One Primary Mode

### DIRECTION

用于：新页面、大改版、用户明确说“太丑 / 太 AI / 重新设计”。

输出：

- Product type
- Primary user/job
- Visual direction
- Primary surface
- Information hierarchy
- Layout strategy
- Allowed / forbidden patterns
- Acceptance target

StoryOS Production Console 默认产品类型：

`Enterprise Control Plane + Operations Workspace + Data Dashboard`

不是 Marketing / Landing Page。

### EXTRACT

用于：已有页面或已有设计系统，需要识别现状后再扩展。

必须识别：

- framework
- theme/tokens
- spacing
- radius
- typography
- status presentation
- table/grid pattern
- drawer/modal pattern
- navigation pattern
- existing shared components

先写“Detected Design Context”，再设计。

### AUDIT

用于：评审截图、已有页面、用户说“看起来很 AI / 帮我评审”。

按严重级别输出：

- Blocker：破坏任务完成或状态识别
- Major：明显 AI Slop、层级/密度/布局问题
- Minor：最多 5 条局部精修

审查必须具体到区域和原因，禁止泛泛说“加强层级”“优化间距”。

### BUILD

用于：设计已明确，需要实现可见 UI。

要求：

- 复用现有 Token / Components
- 主信息优先
- 只加载本任务必要规则
- 不为“漂亮”改变业务逻辑
- 不额外引入 UI 框架

### POLISH

用于：功能已完成，仅视觉精修。

允许：

- typography
- spacing
- alignment
- color restraint
- border/radius
- density
- hover/focus
- visual clutter removal

禁止：

- 改 API Contract
- 改状态模型
- 改页面业务流程
- 顺手重构无关组件

## Design Workflow

### Step 1 — Classify

确认：

- 页面类型
- 主要用户
- 用户主要任务
- 当前是新建 / 扩展 / 重设计 / 评审

### Step 2 — Extract Before Inventing

已有页面必须先提取当前设计语言。

没有证据前，不猜：

- 圆角
- 色板
- 字体
- spacing
- status color
- card pattern

### Step 3 — Define Intent

设计前回答：

1. 页面第一眼应该看到什么？
2. 第二层信息是什么？
3. 哪些信息必须退后？
4. 页面主要靠 Data Grid、Workspace、Timeline、Inspector 还是 Card？
5. 哪些状态值得使用高显著度颜色？

### Step 4 — Anti-AI Gate

实现前检查 `rules/anti-ai.md`。

任何一个页面如果主要依赖：

- 等权卡片
- 大圆角
- 彩色图标块
- 渐变/霓虹
- 胶囊 Badge 海洋
- 解释性副标题
- Bento 乱排

则默认不通过，需要说明业务必要性。

### Step 5 — Apply Visual Hierarchy

顺序：

1. 主角区域
2. Layout / grouping
3. spacing rhythm
4. typography scale
5. semantic color
6. component hierarchy
7. clutter removal
8. shadows / motion last

不要从“选一个漂亮 Card”开始。

### Step 6 — Visual Verification

CREATE / DIRECTION / POLISH 必须执行 `checklists/visual-review.md`。

推荐目标 viewport：

- 1366×768
- 1440×900
- 1536×864
- 1920×1080

如果只能验证一个桌面尺寸，优先当前用户实际目标尺寸，然后说明限制。

### Step 7 — Stop Rule

满足以下条件后停止视觉修改：

- 主次明确
- 页面扫描路径清楚
- AI Slop 主要问题消失
- 状态语义清晰
- 目标 viewport 无明显溢出
- 与 `DESIGN.md` 一致

不要继续为了“还可以更高级”无限微调。

## StoryOS-Specific Heuristics

### Production Monitor

优先级：

`Story/Run Grid > intervention-required exception > queue/concurrency > trace/event > decorative summary`

默认：

- KPI 用 Status Strip，不用卡片墙
- 主表占据最大视觉面积
- Secondary Operations Area 不做等宽四宫格
- Trace/Event 可独立成窄栏或低权重区域

### Run Detail

优先级：

`Run status/current action > pipeline > frame production > metadata`

- Run Detail 优先独立页面，不在 Modal 里再套 Drawer
- Frame 点击后使用 Inspector Drawer
- Production 节点显示内部进度，例如 `14/20`

### Frame Inspector

像 IDE Inspector：

- 最终图 / 当前结果
- status / attempt / duration
- error / retry 信息
- prompt / references / artifact / trace / logs

按钮根据状态动态出现。PASSED 不显示“跳过此帧”。

## External Knowledge Policy

外部 Skill 只用于吸收设计方法，不在 StoryOS 运行时自动拉取最新版本。

当前吸收来源及范围见：

`references/external-skills.md`

更新外部知识时必须：Review → 选择吸收 → 更新本地 Contract → 验证，而不是直接替换本 Skill。

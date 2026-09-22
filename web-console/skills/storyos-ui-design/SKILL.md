---
name: storyos-ui-design
description: StoryOS 专用的去 AI 化与工业级控制台视觉设计规范技能。整合 anti-ai-slop-ui（去 AI 模板味、拒绝等权卡片与霓虹渐变）、mblode/ui-design（Direction/Extract/Audit/Build/Polish 工作流）、Refactoring UI（层级、排版阶梯、色彩与间距原子化决策）、design-md（持久化 DESIGN.md 设计契约）、PracticalSwan（Workspace & Dashboard 控制台模式）以及 interface-kit（高密度控制台工程参数）。
---

# StoryOS UI Design & Anti-AI Slop Skill

本技能是 StoryOS 的核心视觉设计工程工作流。
它定义了从视觉方向设定、既有体系提取、AI 模板坏味道审计、到页面实现与精修的标准五阶段闭环。

---

## 1. 核心定位与原则 (Core Persona & Principles)

StoryOS 前端界面的定位是 **Dense Operations Console / Operations Workbench**（`Product/Workspace` + `Data/Dashboard`）。

- **视觉气质**：克制、专业、高密度、强扫描效率、强信息层级、低装饰、扁平化、状态色语义化、表格优先、Workspace 优先、Inspector / Drawer 优先。
- **严禁**：营销型 SaaS Dashboard、Cyberpunk / AI 霓虹、大量卡片包裹、均等四宫格、泛滥大圆角。
- **质量考核指标**：
  - **AI Slop Risk**：`LOW` (严禁 Medium 或 High)
  - **Distinctiveness Score**：$\ge 8$ / 10
  - **Operational Scanability**：$\ge 8$ / 10

---

## 2. 五阶段工作流模式 (Workflow Modes)

任何前端视觉任务，必须明确当前处于以下哪种模式并按步执行：

```text
       ┌───────────┐
       │ DIRECTION │ 适用于：新页面规划 / 大改版 / 视觉方向不明确
       └─────┬─────┘
             │
       ┌─────▼─────┐
       │  EXTRACT  │ 适用于：已有页面与组件修改前，必须先识别既有 Token 与规范
       └─────┬─────┘
             │
       ┌─────▼─────┐
       │   AUDIT   │ 适用于：页面美化 / 消除 AI 味 / 模板化布局排查
       └─────┬─────┘
             │
       ┌─────▼─────┐
       │   BUILD   │ 适用于：按 DESIGN.md 契约严格实现新模块或界面
       └─────┬─────┘
             │
       ┌─────▼─────┐
       │  POLISH   │ 适用于：功能已完整，纯净微调视觉层级、间距与排版细节
       └───────────┘
```

### 模式一：DIRECTION (方向定义)
**使用场景**：新页面、大改版、视觉方向不明确。
**必须明确输出**：
1. **Product Type**：`Product / Workspace + Data / Dashboard`
2. **Primary User**：StoryOS 运维工程师、短剧/分镜制作人
3. **Primary Job**：秒级定位流水线运行态、排查阻断帧、下发干预指令
4. **Visual Direction**：`Dense Operations Console + Developer Tool`
5. **Information Priority**：主数据网格 > 状态条 > 右侧检视抽屉 > 辅助 Trace
6. **Allowed Patterns**：单行状态条 (56px)、数据网格 (44px 行高)、右侧技术抽屉 (440px)、等宽数字
7. **Forbidden Patterns**：等权四宫格、彩色大胶囊、紫蓝渐变、容器 >8px 圆角、无意义营销文案

### 模式二：EXTRACT (提取既有规范)
**使用场景**：在对任何已有页面动刀前。
**执行铁律**：严禁在未检查现有系统前自行重新造一套 Design System！
1. 读取 `/DESIGN.md` 与 `/src/index.css`；
2. 提取已有 Design Tokens（`--bg-app: #0B0D10`, `--bg-surface: #13161B`, `--border-subtle: #232830` 等）；
3. 提取已有的状态契约（`RUNNING`, `QUEUED`, `RETRYING`, `BLOCKED`, `COMPLETED`）；
4. 识别当前已有布局框架（Sidebar 224px, Header 48px, Status Bar 56px）；
5. 记录任何偏离规范的遗留硬编码。

### 模式三：AUDIT (反 AI 坏味道审计)
**使用场景**：用户反馈“页面太丑”、“AI 味重”、“布局太死板”、“缺乏主次”。
**必须执行清单**：
1. 对照 `rules/anti-ai.md` 中的 20 项清单逐条排查；
2. 对照 `checklists/visual-review.md` 进行打分与风险评估；
3. 输出三级问题列表：
   - **Blocker**：出现等权四宫格、大面积彩色背景、12px+ 大圆角、霓虹发光；
   - **Major**：缺少非对称布局、数字未等宽导致刷新抖动、Card 嵌套过多；
   - **Minor**：间距未对齐 4px 网格、文字对比度微小瑕疵。
**边界注意**：UI 审计仅聚焦视觉层、密度与布局节奏，严禁擅自破坏既有业务信息架构。

### 模式四：BUILD (规范化实现)
**使用场景**：按规范实现新页面或重构界面。
**执行顺序**：
1. 读取 `/DESIGN.md` 获取明确尺寸（表格高度 44px、状态条 56px 等）；
2. 复用已有设计 Token 与原子类，绝不引入外部未经定义的 CSS；
3. 遵循表格优先与非对称布局，建立清晰的视觉焦点；
4. 运行 `checklists/visual-review.md` 自检；
5. 执行编译与 0 报错验证。

### 模式五：POLISH (纯净精修)
**使用场景**：功能逻辑已完全正确，仅微调视觉质量。
**操作铁律**：
- **默认禁止**：改动后端 API、改动数据流与状态机、改动前端 Router、替换外部库；
- **允许调整**：
  - 微调 `padding` 与 `margin` 对齐 4px 网格；
  - 调整文字字阶（`13px / 20px`, `12px / 18px`）；
  - 补充 `font-mono tabular-nums`；
  - 压缩容器边框，以 1px 细分割线替代全封闭边框；
  - 优化高频心跳刷新时的局部重渲染性能。

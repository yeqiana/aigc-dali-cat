# StoryOS Design Language Contract

> StoryOS 可见界面的设计语言唯一入口。Agent 与开发者在新增、改版、评审 UI 前先读本文件。
>
> 这里定义“视觉语义与设计约束”；具体业务事实、状态枚举、API Contract 仍以项目代码与后端 Contract 为准。

## 1. 产品视觉定位

StoryOS Web Console 是 **高密度生产控制台（Dense Operations Console）**，不是营销站、AI SaaS 展示页、数据大屏或赛博朋克看板。

核心气质：

- 冷静、克制、专业、长期可盯
- 高信息密度，但不拥挤
- 强视觉层级，弱装饰
- 表格 / 工作区 / Inspector 优先于 Card Gallery
- 状态色是信号，不是装饰
- 通过 typography、spacing、alignment、divider 建立层级，而不是依赖大量盒子

参考类型只用于理解气质，不要求仿制具体产品：

- IDE / Developer Tool
- Enterprise Control Plane
- Security / Operations Console
- Evidence / Trace Workspace

## 2. StoryOS Visual DNA

固定基线：

```text
Neutral dark workspace
+ compact operational density
+ flat surfaces
+ thin separators
+ strong typography hierarchy
+ semantic color only
+ small radius
+ minimal shadow
+ almost no decorative gradient
```

页面第一目标：让用户在 5–10 秒内回答：

1. 谁在运行？
2. 跑到哪一步？
3. 谁异常？
4. 哪些异常需要人工处理？

任何视觉设计若降低上述扫描效率，应回退。

## 3. Anti-AI UI 原则

默认避免以下组合；只有已有 Design System 明确要求或有清晰业务目的时才允许：

- 每个模块都独立 Card 化
- 一屏大量等宽、等高、等视觉权重卡片
- KPI = 彩色图标方块 + 大数字 + 胶囊状态的模板组合
- 紫蓝渐变、霓虹、发光边框、玻璃拟态
- 所有容器都使用大圆角
- 所有可交互区域都 hover 浮起
- Bento Grid 作为默认布局
- 依靠大量空白假装高级
- 同一页面同时存在过多强调色
- 所有模块都写“标题 + 图标 + 描述 + Card”
- 为“科技感”加入无业务意义动画
- 解释视觉风格的装饰性副标题（例如“Dense AI Operations Console”）

重点检查 AI Slop 信号：

- 页面是否“过于平均”
- 每块是否都被认真包装成独立组件展示位
- 是否缺少真正的主角区域
- 是否主要靠盒子而不是排版建立层级
- 是否为了显得完整加入没有决策价值的说明文字
- 是否用颜色强调了太多本不重要的信息

## 4. Layout Baseline

### 4.1 App Shell

```text
Sidebar expanded:   224px
Sidebar collapsed:   64px
Top header:           48px
Page padding >=1600:  24px
Page padding 1440:    20px
Page padding 1280:    16px
```

桌面优先断点：

- `>=1600`: 完整信息
- `1440–1599`: 标准布局
- `1280–1439`: 隐藏或折叠 secondary columns
- `1024–1279`: Sidebar 默认折叠
- `<1024`: 保证可用，不以移动端体验为 V1 第一目标

### 4.2 页面层级

生产监控类页面推荐结构：

```text
Header
Status Strip
Toolbar
Primary Data Grid / Workspace
Secondary Operations Area
Inspector / Drawer
```

主 Data Grid 必须是页面视觉中心。

禁止默认采用：

```text
KPI Cards
Card Toolbar
Card Table
4 Equal Cards
```

## 5. Color Tokens

颜色最终应进入前端 Theme/Token；新增页面不得自行创建另一套色板。

```css
--bg-app:        #0B0D10;
--bg-workspace:  #0F1115;
--bg-surface:    #13161B;
--bg-elevated:   #171B21;
--bg-hover:      #1B2027;
--bg-selected:   #20262E;

--border-subtle: #232830;
--border-normal: #2D333D;
--border-strong: #3A424E;

--text-primary:   #F1F3F5;
--text-secondary: #A7AFBA;
--text-tertiary:  #737D8A;
--text-disabled:  #505864;

--semantic-success: #3FB950;
--semantic-warning: #C9A227;
--semantic-retry:   #D28B26;
--semantic-danger:  #E05252;
--semantic-info:    #4C8DFF;
--focus-ring:       #58A6FF;
```

规则：

- 绿色不是 StoryOS 品牌色，只表达成功/健康语义。
- 红色保留给 Blocked / Failed / Critical。
- 状态色优先作用于 dot、文字、2px marker、细进度线，不大面积铺底。
- 不允许同一状态在不同页面自行换色。

## 6. Spacing / Radius / Border

使用 4px Base Grid：

```text
4 / 8 / 12 / 16 / 20 / 24 / 32 / 40
```

常用规则：

- 组件内部：8 / 12
- 组件之间：16
- 区域之间：24
- 大区块：32

Radius：

```text
xs 3px
sm 4px
md 6px
lg 8px
```

默认：

- Badge 4px
- Button/Input 5–6px
- Table/Panel 6px
- Modal 8px
- Drawer 0

禁止无业务理由使用 12/16/20/24px 大圆角。

Border：`1px`。普通 Panel 不使用 Shadow。

## 7. Typography

字体策略：优先系统 UI 字体，运行数据使用 Mono；不得为“高级感”随意引入字体依赖。

```text
UI: Inter / SF Pro Text / PingFang SC / Microsoft YaHei / sans-serif
Mono: JetBrains Mono / SFMono-Regular / Consolas / monospace
```

建议层级：

| Role | Size | Line Height | Weight |
| --- | ---: | ---: | ---: |
| Page title | 20 | 28 | 600 |
| Run title | 18 | 26 | 600 |
| Section title | 14 | 20 | 600 |
| Primary data | 13 | 20 | 500 |
| Body | 13 | 20 | 400 |
| Metadata | 12 | 18 | 400 |
| Small status | 11 | 16 | 500 |
| Runtime mono | 12 | 18 | 400 |

强制视觉排序：业务实体 > 当前状态/动作 > 关键数字 > 元数据 > 技术 ID。

Run ID、Trace ID、时间戳等不得与 Story 名称争夺视觉权重。

## 8. Operational Status Strip

生产监控 KPI 默认不使用 6–8 张独立 Card。

推荐：一条 48–64px 的 Operational Status Strip。

```text
运行中 4 | 等待 2 | 重试 3 | 阻塞 1 | 今日完成 18
并发 4/4 | Queue 26 | Runtime Healthy
```

- Label: 11–12px tertiary
- Value: 16–18px / 600
- 组间距：20–24px
- 只使用 divider / spacing 建立分组

## 9. Data Grid

StoryOS 多任务监控的 Primary Surface = Data Grid。

```text
Header: 36px
Row: 44px
Compact row: 40px
Cell X padding: 12px
Cell Y padding: 8px
Header font: 12px / 500
Primary font: 13px
Secondary font: 12px
```

默认：

- Row 只保留底部分割线
- Hover 使用轻背景变化
- Selected 使用低对比背景 + 可选 2px marker
- 不让整行因为 RUNNING 变绿
- 异常才允许显著视觉跳出

## 10. Status Presentation

状态默认形式：

```text
● Running
● Waiting
● Retrying
● Blocked
● Completed
```

- Dot: 6px
- Gap: 6px
- Text: 12px / 500
- 默认无大面积 Badge 底色

需要背景时透明度应非常低，只用于小面积辅助。

状态语义必须来自项目 Contract；前端 UI 不得因请求失败把业务 RUNNING 误显示为 FAILED。

## 11. Controls

```text
Small button: 28px / 12px font / 10px x-padding
Default:      32px / 13px font / 12px x-padding
Large:        36px（少用）
Input/Select: 32px
Toolbar:      40–48px
```

- Primary Button 只给真正主动作。
- 查看、日志、Trace、Artifact 优先 Text/Ghost/Secondary。
- Dangerous Action 才使用 Danger。
- Icon-only 必须有 accessible name。

## 12. Inspector / Drawer

Frame / Run Inspector 应像 IDE Inspector，不像电商详情弹窗。

```text
Default width: 440px
Detail width:  520px
Max width:     640px
Header:         56px
Padding:        20px
Section gap:    24px
Radius:          0
Border-left:     1px
```

原图按需加载；不要让 Drawer 打开导致主工作区重置或整页刷新。

## 13. Pipeline

- 节点高度：56–64px
- 节点最小宽：120px
- 连接线：1px
- 当前节点通过 marker、dot、文字层级强调，不使用大面积发光
- Production 等长阶段可以在节点内展示 3px progress + `14/20`

## 14. Frame Grid

20 Frame 默认桌面 5 列，`12px` gap。

- Card radius: 4–6px
- Border: 1px
- 状态只作用于 dot / label / small marker
- Hover 提升 border contrast，不做浮起动画
- RUNNING 显示当前 action + duration
- RETRYING 显示 attempt，而不是只显示耗时

## 15. Secondary Operations Area

不要默认使用四个等宽等高 Panel。

优先：

- 非均质比例，例如 `1.5fr 1.2fr 1fr 1fr`
- Trace / Event 可作为右侧窄工作栏
- Worker / Queue / Exception 根据业务重要性获得不同面积

一致性来自 token 和对齐，不来自“所有块一样大”。

## 16. Motion

StoryOS 不做 Motion Showcase。

```text
Hover:    120ms
Dropdown: 140ms
Modal:    160ms
Drawer:   180ms
Easing:   cubic-bezier(.2,.8,.2,1)
```

禁止默认使用：弹跳、spring 炫技、呼吸灯、背景流光、持续闪烁。

`prefers-reduced-motion` 必须尊重。

## 17. Content / Chrome Hygiene

删除无决策价值的界面文字。

例如以下文案默认不应出现：

- “Dense Operations Console · 高密度生产调度”
- 解释当前页面视觉风格的标语
- 每个 Panel 下重复解释显而易见的功能

文案存在的理由必须是：帮助理解状态、完成任务、避免误操作。

## 18. Visual Review Gate

任何 CREATE / VISUAL REDESIGN / POLISH 在宣告完成前必须进行视觉验收：

1. 页面主角是否明确？
2. 是否存在过多等权 Card？
3. 是否通过盒子而不是排版建立结构？
4. 是否有无意义副标题/说明？
5. 状态色是否过量？
6. Typography 层级是否足够强？
7. Secondary 信息是否真正退后？
8. 1366 / 1440 / 1536 / 1920 是否可扫读？
9. 长文本、空数据、异常、极端数字是否破坏布局？
10. 页面是否仍像通用 AI Dashboard？如果是，不通过。

视觉 QA 最多执行：一次完整审查 → 一批集中修复 → 一次确认。禁止无休止 2px 微调。

## 19. Source of Truth

优先级：

1. 用户当前明确要求
2. `AGENTS.md` / 项目强制约束
3. 后端 / Runtime / API Contract
4. 本 `DESIGN.md`
5. `storyos-ui-design` Skill
6. 当前模块稳定模式
7. 外部 Skill / 公开参考
8. Agent 自身偏好

外部 Skill 永远只是参考知识，不直接决定 StoryOS UI。

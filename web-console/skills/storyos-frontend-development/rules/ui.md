# StoryOS UI Baseline v1 (Dense Operations Console)

本规范为 StoryOS 生产监控台及全部后台界面的视觉 Token、尺寸、密度与组件度量基线，已被系统纳入严格门禁。

## 1. 核心定位 (Core Archetype)
- **Dense Operations Console / 高密度生产控制台**；
- 属性：高信息密度、低装饰、扁平层级、小圆角、弱边框、强排版层级、状态色克制、表格与 Inspector/Drawer 优先；
- 拒绝：SaaS 营销页大卡片、科幻发光仪表盘、纯黑纯绿科技大屏。

## 2. 核心 Token 契约

```css
:root {
  /* Background (严禁私自混用蓝黑/紫黑/绿黑/渐变黑) */
  --bg-app:        #0B0D10; /* L0: App Background */
  --bg-workspace:  #0F1115; /* L1: Workspace */
  --bg-surface:    #13161B; /* L2: Surface / Table / Panel */
  --bg-elevated:   #171B21; /* L3: Elevated / Modal / Inspector */
  --bg-hover:      #1B2027; /* Table row hover */
  --bg-selected:   #20262E; /* Selected row */

  /* Border (1px 统一宽度，禁止彩色炫光边框) */
  --border-subtle: #232830;
  --border-normal: #2D333D;
  --border-strong: #3A424E;

  /* Text Hierarchy */
  --text-primary:   #F1F3F5;
  --text-secondary: #A7AFBA;
  --text-tertiary:  #737D8A;
  --text-disabled:  #505864;

  /* Semantic (克制表达，非品牌色) */
  --success: #3FB950;
  --warning: #D29922;
  --retry:   #E3A008;
  --danger:  #F85149;
  --info:    #58A6FF;

  /* Focus & Selection */
  --focus: #58A6FF;

  /* Radius (严禁 12/16/20/24px 大 SaaS 圆角) */
  --radius-xs: 3px;
  --radius-sm: 4px;  /* Badge, Tooltip */
  --radius-md: 6px;  /* Button, Input, Table, Panel */
  --radius-lg: 8px;  /* Modal */
  --radius-drawer: 0;

  /* Space (4px Base Grid) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;

  /* Layout & Metrics */
  --sidebar-width: 224px;
  --sidebar-collapsed: 64px;
  --header-height: 48px;

  /* Components Metrics */
  --control-height: 32px;
  --table-header-height: 36px;
  --table-row-height: 44px;
  --table-row-compact: 40px;
  --drawer-width: 440px;
  --drawer-detail-width: 520px;

  /* Motion */
  --motion-fast: 120ms;
  --motion-normal: 180ms;
}
```

## 3. 组件级严格尺寸与规则

### 3.1 KPI Operational Status Bar（严禁 6 张大 Card 堆砌）
- 形式：高度 56–64px 的连续单条 Operational Bar；
- 结构：`运行中 4 | 等待 2 | 重试 3 | 阻塞 1 | 今日完成 18`；
- Label：11px / tertiary；Value：18px / 600；Divider：1px `#232830`。

### 3.2 Data Table（生产监控台核心）
- Header height: 36px (12px, font-medium, text-secondary)；
- Row height: 44px (Primary 13px, Secondary 12px)；
- Padding: Cell X 12px, Cell Y 8px；
- 分隔线：`border-bottom: 1px solid #232830`；
- Hover: `#1B2027`；Selected: `#20262E`（左侧 2px selection indicator，严禁整行发光）。

### 3.3 状态 Badge
- 形式：`● Running`、`● Blocked`（禁止铺满浓艳背景的大胶囊）；
- 尺寸：dot 6px, gap 6px, font 12px / 500；
- 背景：仅限 ≤ 8% 超低透明度或直接无背景。

### 3.4 控件与按钮 (Buttons & Inputs)
- Small: height 28px, padding 0 10px, font 12px；
- Default: height 32px, padding 0 12px, font 13px；
- Large: height 36px；
- 严禁 40–48px 巨型按钮；常规查看/日志/追踪优先使用 Ghost / Secondary。

### 3.5 Inspector / Frame Drawer
- Width: Default 440px, Detail 520px, Max 640px；
- Radius: 0 (直角帖边)；Border-left: 1px solid `#232830`；
- 像 IDE Inspector 一样紧凑，严禁电商详情弹窗样式。

### 3.6 盒子数量控制 (Anti-Card Rule)
- 严禁在同一视口内用 Card 套 Card、Card 堆 Card；
- 结构走向：`Header ➔ Operational Status Bar ➔ Toolbar ➔ Data Grid ➔ Operations Strip`。

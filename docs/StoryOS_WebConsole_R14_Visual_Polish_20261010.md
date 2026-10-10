# StoryOS Web Console R14 视觉品质与一致性整改验收（2026-10-10）

## 目标与视觉评审

反馈：R13 虽然接入开源组件、去掉大型卡片与增加分页，但页面仍存在字号偏小、无效信息过多、数据源机器字段直接铺在表格、多个独立样式系统混用，导致视觉品质不一致。

按照 `DESIGN.md` 的 **Dense Operations Console** 执行，强调：清晰的层级、可靠证据、主列表优先、紧凑但可读；禁止再引入展示型 Dashboard、大圆角和装饰性数据。

## 四隔离槽位交付

1. **壳层与 Design Tokens**：`Sidebar` 统一为 224px、Header 52px、品牌标识与导航间距收敛；`index.css` / `theme.ts` 统一暗/亮/亮渐变三主题的文字对比度、分隔线与选中态；`AntdSurface` 使用同套 Theme Tokens 约束 Table / Pagination / Button 的表头、单元格行高和间距。
2. **首页与作品库**：删掉无意义的英文装饰眉题和无法核验的第 4 个指标；首屏仅保留项目、故事、待继续三个指标；作品列表使用更清晰的一级标题、阶段与帧数；作品库日期进行简短人类可读呈现，采用 Ant Design Progress，不再造进度条。
3. **生产监控与工作流**：监控历史 Run 用 Ant Design Table 替代手写表格；顶部权威状态记录也改为 Table（作品、阶段、来源、详情），保留原只读详单 API 与分页/加载更多逻辑；合并重复来源说明，不再将旧的心跳表示为在线。工作流表格的来源与时间字段改为人类可读显示，保留 title 中的原始字段。
4. **Agents、设置与日志**：Agent Registry 不可连接时用 Ant Design Alert、Empty 与重试按钮，拒绝伪造能力或数据；调整 Memory、设置与日志的文字层次、控件高度和间距。

## 可靠性与数据边界

- 本地 `episode-state.json` 记录经过只读 API 显示；来源为 `local_workspace_episode_state_file`，不是 MySQL/Redis 在线 Runtime、队列或 Worker 真实心跳。
- 表格从 API/既有历史快照获取真实记录，不生成模拟记录、不更改业务状态、不执行生产/生图/发布/审核写入。
- 保留 Ant Design 组件和路由懒加载，不创建另一套通用 UI。
- 主分支合并前必须保留全部已有未跟踪文件与素材。

## 浏览器验收

- 四个独立工作树分别执行 TypeScript `npm run lint` 和 Vite build，均通过；集成分支重新验证 API、Monitor、Workflow、Console、Episode/Run 数据一致性、只读探测、可访问性等核心契约。
- 真实磁盘数据 Chrome 视觉检查：R10 首页/监控/工作流/1366px 桌面、R11 作品库/Agents/日志/设置、R12 故事制作/历史 Run 详情、R13 首页/作品库/工作流/监控分页与主题切换。深度用例中的历史 Run 入口需明确定位历史表（`storyos-monitor-grid`），不能因新增权威状态表误点其他列表。
- Chrome 截图生成于 Git 忽略目录 `.storyos-tmp/ui-qa/r10`、`r11`、`r12`，不写入仓库。

## 后续仍待优化的实质问题

部分故事制作详情没有可靠的缩略图资产，仍会出现文件缺失占位；这不是加样式能解决的问题，需要先核实资产路径及授权的读取 API。其他深层操作若无后端授权契约，维持只读状态。

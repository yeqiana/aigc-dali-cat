# StoryOS Web Console R11 品牌与布局统一验收（2026-10-10）

## 用户要求
浏览器标签仅显示 **StoryOS**，弃用原 E 形占位图标；重设计 favicon，并继续整改其他页面不美观、布局不合理、信息层级弱的问题。

## 设计约束
遵守 `DESIGN.md`、`skills/storyos-ui-design/SKILL.md`：高密度、平面化、弱阴影、视觉先主列表后辅助信息；不新增营销风格卡片墙或误导性的“实时运行”状态。所有改造均为只读前端，不改 Runtime/API 业务语义。

## 四槽并发交付
- **品牌/入口**：`web-console/index.html` 的 document title、application-name、OpenGraph title 统一为 StoryOS；更新 SVG favicon，采用深色方形、白色 S 轨迹与蓝色起点。侧栏新增 `StoryOSMark.tsx` 复用同形标识，删除解释性品牌副标题。
- **作品库**：`SeriesLibraryView.tsx` 采用紧凑数据行和清晰列标题，优化标题/阶段/时间/帧数权重。同步修复 `App.tsx` 外层 `max-w-4xl` 导致宽屏列表被压窄的问题。
- **Agents/Memory**：`AgentWorkspaceView.tsx`、`MemorySearchPanel.tsx` 减少等权盒子与多余留白，把真实 Registry 查询与错误状态放在主要位置。
- **设置/日志**：`SettingsView.tsx` 补充页面标题、优化主题选择布局，给两个图标开关增加 `aria-label`、`aria-pressed`；`RuntimeLogsView.tsx` 去掉不准确的绿色“实时捕获”动效，改为真实的自动轮询/手动刷新说明，调整搜索与操作栏排版。

## 质量验收
- 四隔离工作树分别完成 TypeScript、Vite build 和 Git diff --check。
- 合并候选分支执行 lint/build、Bundle、Episode/Run 数据一致性、API/监控/Workflow/console/readonly 等回归。
- Chrome 本机真实文件只读模式 `127.0.0.1:3103`；标题/favicon HTTP 200，API 返回 `local_workspace_episode_state_file`，20 条磁盘记录（非 MySQL 在线 Runtime）。
- Browser A/B：原工作台/监控/工作流/1366px 的 4 项视觉回归；新增作品库/Agents/日志/设置的 4 项标题、布局溢出、可访问性与截图回归。
- 截图存于忽略目录 `.storyos-tmp/ui-qa/r11`，不写入仓库，原始素材和证据不改。

## 未解决项
- 其他复杂的故事制作子组件与生产监控深度 Inspector 尚待逐一截图精修；本轮不擅自改变其状态、API 或审核语义。
- 本地文件证据是只读磁盘快照，不代表 MySQL 权威实时 Worker 状态。

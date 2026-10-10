# StoryOS Web Console R13：开源表格 / 全宽列表 / 分页整改验收

日期：2026-10-10

## 要求与取向

移除大片留白与非必要卡片，列表占满工作区可用宽度；需要分页的长列表加分页。使用成熟开源 UI 组件，而不手搓普通 Table、Pagination、Select、Input。坚持根目录 `DESIGN.md` 中紧凑、列表优先的运行台规范，深浅模式仍一致。

## 开源依赖

- 正式新增 `antd@6.6.5`（开源 Ant Design），锁定在 `web-console/package-lock.json`。
- 用 `ConfigProvider` 的 compact 组件尺寸、标准 Table / Pagination / Steps / Input.Search / Select / Button。
- `AntdSurface` 由 React.lazy 按路由加载，根据现有 `theme-dark / theme-light / theme-light-gradient` 同步组件库主题，避免首屏一次加载整库。
- 构建主入口压在现有 350KB 门槛内，历史 Episode 和 Run 的 11+11 个懒加载切分保持。

## 页面落实

| 页面 | 整改 | 分页规则 |
| --- | --- | --- |
| 工作台 | 去除大面积 Hero 卡片、统计墙改薄的分隔指标条；真实状态与故事列表整行展示 | 平台返回记录按已加载数量分页 10/页；故事列表 10/页 |
| 作品与项目 | 去掉中心 max-width、卡片列表改为 AntD Table；统一搜索、阶段筛选 | AntD Table 内建分页，默认 10；筛选后重置第 1 页 |
| 生产流程 | 移除 7 个等权大卡，改 AntD Steps + 宽表格 | AntD Table 默认 15；服务端另用“加载更多”，两种分页语义明确区分 |
| 生产监控 | 摘要/工具栏扁平化、历史 Run 表占满宽度 | 快照表 10/页；筛选后重置页码 |
| 平台阶段证据 | 保留来源警告和读端状态，替换“展开8条” | 已载入数据 AntD 分页 10/页，服务端加载下一页为独立按钮 |
| Agents | 删除三等权能力卡，改 AntD Table 与 Registry 错误信息 | Table 默认 15/页，真实已加载 Agent 数量 |
| 审计日志 | 保留专业日志专用网格/筛选/Inspector，替换自绘分页导航 | AntD Pagination 支持 15/20/50/100 和筛选后页数钳制 |
| 系统设置 | 删除大型主题预览卡与不生效的模拟表单，保留真正能切换主题的 AntD Tabs + Segmented | 无长列表；生产配置仅展示未接入说明，不伪造 RUNNING / 已保存 |

## 数据边界

- 本机 `local_workspace_episode_state_file` 是真实磁盘证据，不是 MySQL/Redis 或在线 Worker 心跳。
- `API has_more` 未清零时，不能显示“已加载全部”；客户端分页只翻**已取回的数据**，继续加载服务端记录需显式调用原只读 API。
- 过滤、页长变化均作用于实际行数据；不可只更换分页 UI 而没有切换数据。
- 不执行审核 PASS / 生图、发布或 Runtime 阶段推进；不修改原始故事素材。

## 本轮验收

- 四个隔离槽独立 TypeScript 构建无错。
- 集成 Vite/TypeScript/build 和现有 Bundle/Episode/Run/HTTP/Workflow/monitor/console 契约回归。
- 深色真实状态文件浏览器：R10 4/4、R11 4/4、R12 深层页面 2/2。
- R13 新增浏览器真实交互测试 `npm run test:paging`，Chrome 点击首页、作品库、工作流、监控“下一页”，4/4；无页面横向溢出。
- `npm run test:theme` 实测新设置页 AntD Tabs/Segmented，切浅色后再切深色，两次主题状态同步通过。
- `test:workflow` 的旧 `file://` fixture 被改为一次性本机 HTTP 静态服务，仍断言只取一次下一页、API 离线明确失败；本机测试服务在任务结束后释放。
- 截图与失败 DOM 全部写 Git 忽略的 `.storyos-tmp/ui-qa`，不进入仓库。

## 后续

仍需按页面审查故事创作子模块的多栏编辑需求、历史 Run 图片资产的占位图加载问题；不能用“UI 全宽”替代真实资产和权限合同。

# StoryOS Web Console UX 重新设计（2026-10-10）

## 设计目标
由密集的单一技术监控页，重构为面向日常创作与专业运维的分层工作区：普通使用者在工作台与故事制作页获得清楚的下一步，运维人员在监控/日志页迅速找到阻塞。保留根 DESIGN.md 对 4px 网格、语义状态、表格扫描效率的要求，不使用彩色 KPI 卡片墙。

## IA / 路径
- 工作台（默认）：最近作品、真正的审核阻塞证据、快速新建、跳转监控。
- 作品与项目：可搜索的故事库、进度、进入作品制作。
- 故事制作：ProductionMetrics、批次帧、逐帧审核、右侧 Context Inspector。
- 生产监控：主 Grid 优先，显示运行证据来源；不允许前端假暂停/恢复/重试。
- 工作流：7 个 canonical stage 及真实状态 summary，前端只读。
- Agents：API 注册清单及明确的未接入状态，不伪造 Agents、Skills、MCP 或 Memory 数量。
- 审计日志 / 设置：保留原有业务入口。

## 接口能力矩阵
| 能力 | 已知前端 API | 新界面原则 |
|---|---|---|
| 阶段列表 | GET /api/v1/runtime/statuses | 使用 summary；不推断 Worker |
| 阶段详情 | GET /api/v1/runtime/status | 展示 detail，缺字段标未提供 |
| Agent 列表 | GET /api/v1/agents 当前后端未注册 | 404 作为未接入提示，不当作运行失败 |
| Skills/MCP Registry | 尚未提供可证实前端端点 | 仅能力说明，不造数据 |
| 暂停/重试/帧通过 | 无已验证写入契约 | 禁止前端模拟变更和成功提示 |

## 四槽位集成契约
S1 负责 App、Sidebar、Home；S2 负责 ProductionMonitorView / RunDetail；S3 负责 ActivityStream / Metrics / SeriesLibrary；S4 负责本文件与 AgentWorkspaceView、WorkflowWorkspaceView。S4 两组件均 named export、零必填 Props；S1 负责统一挂载路由。请勿跨槽覆盖。

## 验收
- TypeScript lint 与 vite build 均通过；1366/1440/1920 宽度无水平大溢出。
- 作品名称、主操作、异常优先级在第一视线可识别；空态与 API 错误不显示假成功。
- 所有前端阶段、审核、生成操作不得无 API 情况下更改权威状态。
- UI 不因装饰卡片、渐变或胶囊色块损害可扫描性。
- 原有用户项目、历史记录不得因视觉改版被删除。

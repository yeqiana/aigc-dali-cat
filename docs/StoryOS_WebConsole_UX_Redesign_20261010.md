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

## 2026-10-10 实施与验证记录
- 四个独立 Worktree 完成各自限定文件，并已 cherry-pick 到 `feature/storyos-webconsole-design-shell-20261010` 作为待评审集成分支。最终集成提交为 `700c87f7`（后续可有文档提交）。未触碰主工作树的生产状态和未提交变更。
- `npm run lint` (`tsc --noEmit`) 通过；`npm run build` (`vite build`) 通过。构建存在打包 chunk 超过 500KB 的非阻塞警告，后续建议延迟加载大型监控视图。
- Chrome headless 使用相对资源构建（`vite build --base=./`）对静态入口分别在 1366×900、1440×900、1920×900 验证首页，截图保存于当前集成工作树忽略目录 `.storyos-tmp/ui-qa/storyos-overview-{1366,1440,1920}.png`。页面可渲染，导航、主体列表、关注区无明显水平溢出。**该检查是截图级静态冒烟，不等于用户交互自动化测试。**
- Vite preview 在当前 Runner 宿主启动时出现 `listen EACCES`（3100/3112），未执行真实 Platform API 联机端到端浏览器验收。Agents API 当前无已知权威列表契约，断连时显示能力未接通；流程与监控对无受控写 API 的操作禁用或提示未执行。
- Runner 当前不支持 WebCodex `coding_agent_runs`，而本机原生 `codex login status` 未登录。四槽改动由 WebCodex 直接在四个 Worktree 中完成，不能声称同时启动四个自主 Coding Agents。

## 待后续验收
1. API 可用环境下逐页点击、搜索/筛选、弹窗键盘、错误/加载/空态，以及单个 Story 的完整业务流程。
2. 审核和生成等受控写入 API 打通后，以真实后端回执恢复操作并补充 E2E，不得恢复前端自写的假成功。
3. 评估按路由进行代码拆包优化，完成 1366/1440/1920 下的生产监控、作品页、Agent 页截图审查。

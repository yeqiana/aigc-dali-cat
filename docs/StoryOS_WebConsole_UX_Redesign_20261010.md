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
## 第二轮四槽并行改造与验收（2026-10-10）

### 分槽交付（四个独立 Worktree，均从 44e687d6 派生）
- 槽 1：工作台搜索 / 导航可访问性：eab1e402（集成 f255b930）
- 槽 2：生产监控 API / 快照区分、心跳、异常与阶段筛选、同名匹配安全：61c02c6e（集成 83711c9b）
- 槽 3：作品证据检视改版：取消虚构费用、生产账本、发布放行、假导出；提供真实工作区 JSON 复制与下载：bdbbed75（集成 f74affbc）
- 槽 4：按视图拆包（React.lazy）、仅本机持久化的故事草稿（不再继承其他作品的人物 / 评分 / 生产状态）、Workflow 权威摘要分页：80f73064（集成 1ca60462）

### 质量与浏览器验证
- 四个独立槽位均通过 npm run lint (tsc --noEmit) 与 npm run build；合并后再次 lint / build 全通过。已执行 git diff --check。
- Vite 打包后主入口 JS 约 1.24 MB（gzip 约 179 KB），较前一轮约 1.73 MB（gzip 314 KB）下降，但仍有超 500 KB chunk 警告，不能宣称包体积问题完全解决。
- 本机 Chrome headless 通过静态构建文件的实际导航点击冒烟：Agents、工作流、生产监控、故事制作，4/4 通过。
- 通过新建本机草稿、输入标题、提交、刷新后再次查找的浏览器持久化冒烟（1/1）。
- 在 1366×900、1440×900、1920×900 下生成首页静态截图，保存在当前集成 Worktree 的忽略目录 .storyos-tmp/ui-qa/storyos-r2-home-{1366,1440,1920}.png。1440 尺寸已目视确认标题、表格、导航和关注区没有明显水平溢出。
- 所有浏览器验证均以 vite build --base=./ 构建的本地静态文件执行。没有写入真实生产，也不依赖付费模型。

### 仍需单独验收
- 实时 Platform API 连接及健康、并发、队列真实值；当前监控仅可审阅历史运行快照与权威 stage summary，二者不得混成一个实时状态。
- 受控写入端点未确认前，暂停 / 重试 / 阶段推进 / 质检放行仍必须保持不可执行。草稿仅写入浏览器 Local Storage，不代表创建正式 Episode。
- 真实 API E2E、详细页每一个交互、自动化无障碍扫描和各主视图多分辨率截图未完成；本轮静态路由冒烟不能代替这些验收。
## 第三轮四槽迭代（2026-10-10）

### 四槽隔离交付
- 槽 1：工作台直接读取 /api/v1/runtime/statuses 的阶段摘要，并标注读取时间、部分失败和断连状态；独立提交 d0269dc4，集成 ae23e545。
- 槽 2：生产监控新增 RuntimeAuthorityPanel；从 Runtime API 获取阶段列表，逐作品 GET /api/v1/runtime/status 查询执行状态、阻塞、心跳与帧数。历史工作区 Run 表独立显示，不按标题把 API 阶段混写进去；独立提交 9a07c6a6，集成 5f11421c。
- 槽 3：故事制作页增加 StoryNextAction。根据工作区 Frame Review 与 Preflight 记录区分草稿、阻塞、待确认、无审核记录，绝不直接驱动生产；独立提交 f011247e，集成 8e8af325。
- 槽 4：Agent 页面新增 MemorySearchPanel，通过现有 POST /api/v1/memory/search 检索经验（需用户主动输入）；Workflow 列表增加逐作品权威详情查看，独立提交 63257665，集成 c5052b87。
- 集成精修：草稿判断只依据本机新建草稿 ID；制作阶段明确标注“工作区投影，正式阶段以 Runtime API 为准”。

### 已验证
- 四个独立 Worktree 各自执行 npm run lint + npm run build，全部通过；集成分支另行通过 TypeScript、vite build --base=./ 与 git diff --check。
- Chrome 静态构建 + **模拟 Platform API 响应** 的五项交互冒烟 PASS：home 阶段摘要、monitor 权威 Run 详情、workflow 阶段详情、Agents Memory 检索、story 下一步提示。测试中的“权威阶段样例”仅是注入在测试页面的桩数据，不属于真实业务库。
- 生成并检查 1366×768 首页、1440×900 首页、1440×900 监控、1440×900 Workflow、1920×1080 Story 截图；Workflow 首次截图在懒加载中，延长等待后重拍并检查实际页面。截图保存在集成 Worktree 的 Git 忽略目录 .storyos-tmp/ui-qa/。
- 本机健康检查 GET http://127.0.0.1:8080/healthz 当前不可达，未进行真实后端 E2E；本轮不能把模拟响应成功当作 Platform API 联调完成。

### 未解决 / 下一轮
- 正式部署环境的真实 API 联调、分页边界、稳定身份与变更权威验收；正式生产写操作必须先拿到明确授权 API 契约。
- 主入口 JS 仍约 1.24MB（构建原始值），超过 Vite 500KB 提示线。需定位内容静态快照和依赖的具体占比后再拆包。
- 需要可重复执行的正式浏览器 E2E、失败注入测试、无障碍检查与项目级数据一致性审查。

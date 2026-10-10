# StoryOS Web Console R12：工作台、Run Inspector、审核组件与视觉契约验收（2026-10-10）

## 设计依据
遵守根 `DESIGN.md` 与 `skills/storyos-ui-design/checklists/visual-review.md`：页面以生产证据和状态扫描为中心，减少多余卡片、14px 大圆角与装饰阴影；历史作品与 Run 状态始终不冒充在线 Worker/Runtime。

## 四槽并发内容
- **故事工作台**：`ActivityStream`、`ProductionMetricsPanel`、`StatusFlowBanner` 减少卡片层级和长行，支持更多分镜横排；制作进度来自 `Episode` 字段，不推断放行。
- **Run 详情**：`StoryRunDetailView` 缩减横向溢出风险；默认不自动选中演示 Frame09；历史快照心跳不可判断在线健康；不再默认显示 Worker-01、14s 时长或固定的 14/1/1/4 状态统计；细节计数按 `run.frames` 计算。顶栏不可暂停/恢复的功能改成只读说明，通过帧数和通过帧率直接从 `run.frames` 中的 `PASSED` 记录统计，避免历史汇总字段 `completedFrames` 滞后出现 0/20 与逐帧 20/20 矛盾，避免出现 20/20 帧却显示 0% 的歧义；图标-only 操作增加 aria-label。
- **审核组件**：`StoryboardProgressCard` 根据传入 beats 动态分幕，避免预设四幕进度；`PreflightCheckCard` 避免固定“24/32、Frame18、28–32”阻塞与假发布按钮；`FrameReviewCard` 不再用定时器模拟修补成功并修改 PASS，展示传入证据的只读审核列表。
- **Shell / Context Inspector**：`App.tsx` 故事制作主轴增宽到 1100px；侧栏保留原导航与搜索；`ContextPanel` 改为更紧凑的 304px 只读检视列，>=1536px 才展开；公共卡片 token 收敛到 6–8px 圆角、无装饰性阴影，按钮和状态提示按 Design Contract 统一。

## 验收
- 四独立分支各自执行 `npm run lint`、`npm run build -- --base=./`、`git diff --check`。
- 集成分支执行 Bundle、Episode、Run、API、监控、Workflow、Console、只读探测、可访问性等既有回归。
- `npm run test:workbench-run`：连接本机磁盘只读证据 API，Chrome 1366px 故事制作、1440px 历史 Run 详情逐页验收，检查标题、内容、来源、按钮名称和水平溢出；截图存入忽略路径 `.storyos-tmp/ui-qa/r12`。
- R10/R11 原有视觉回归分别验证概览、监控、工作流及作品库、Agents、日志、设置页；本轮不修改真实数据库或生产驱动，不派发图像生成任务。

## 实际范围与后续
- 上述三个旧审核组件暂非主 Workbench 直接挂载组件，但已修复其视觉和假操作风险；真实主 Workbench 使用 `ActivityStream`、`ProductionMetricsPanel`。
- 本机文件快照是真实作品证据，但不等于 MySQL/Redis 权威实时 Runtime；其他旧的详单深层次操作仍需单独 API 授权合同再接入。

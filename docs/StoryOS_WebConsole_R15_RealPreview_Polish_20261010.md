# StoryOS Web Console R15：真实图片占位与创作空间收敛验收（2026-10-10）

## 任务范围

基于 R14 的控制台与 `DESIGN.md`，优先恢复本地 `3100` Web Console 与只读 `19117` 文件证据 API，确认记录来源后处理深层界面的灰色占位图、过于拥挤的历史详情及长期占屏幕的草稿编辑区。本轮不开启正式 Runtime、不生成图片、不连接生产数据库、不执行付费任务。

## 启动验证

- 使用 `web-console/scripts/launch-local-real-console.mjs` 启动，Web Console `http://127.0.0.1:3100/`，只读证据 `127.0.0.1:19117`。
- 实测主页 HTTP 200、API HTTP 200，读取 `20/20` 条本机 `episode-state.json` 记录，`state_source=local_workspace_episode_state_file`。
- 该来源不是在线 Worker/队列/心跳，仅能代表已保存的磁盘证据。

## 4 槽整改

| 槽位 | 改动 | 用户可感知变化 |
| --- | --- | --- |
| 批次预览 | `ActivityStream.tsx` | 当批次没有可验证图像时，20 张大灰图替换为两排紧凑、具备帧编号与状态的网格；有真实预览的记录仍按竖图展示 |
| Run 详情 | `StoryRunDetailView.tsx` | 将冻结快照中的通用 `data:image/svg+xml` 示意图视为“无原图”，移除误导性的全屏原图操作；保留帧状态与审计数据 |
| 制作操作 | `CommandDock.tsx`、`StoryNextAction.tsx` | 未发送的生产指令草稿默认折叠，占屏幕高度显著缩小；显式展开编辑后仍支持复制，绝不冒充下达生产命令 |
| 作品目录 | `HomeOverviewView.tsx`、`SeriesLibraryView.tsx` | 假 SVG 图不再当作品封面展示，改回中性的无预览标识；可用真实图时不受影响 |

## 审计真实性修复

在历史 Run 详情中，删除无记录时擅自推断的 `worker-node-01-eu`、`NVIDIA A100-SXM4-80GB`、`5000 ms`、`4 Slots`、`gpt-image-2.5-flare`、`flux-cinematic-pro`、`33s` 和 `4.2MB` 默认值。此类字段改为“未提供/大小未知”，不推断在线生产状态。

本次**没有直接将 episodes/ 下的真实 PNG 路径暴露给浏览器**。虽然磁盘上存在 approved 与 candidate 素材，但当前 API 合同仅允许读取阶段状态；将真实图片映射到网页需要单独实现受限的媒体资源读端，并做目录越界、候选/已审核可见性和身份对应验收，不能用随意映射或任意文件服务代替。

## 验收与安全边界

- 四槽各自 `npm run lint` 与 Vite build 均通过。
- 集成 `lint`、`build`、`test:bundles`、`test:episodes`、`test:runs` 通过，11 部历史作品及 11 组 Run 快照按原始字段一致。
- 使用 `3107` 隔离预览 + `19117` 本机真实只读 API：R10 页面 Chrome 4/4；R12 工作台 / Run 详情 2/2；真实翻页 4/4；浅色/深色主题切换通过；离线状态 5/5；基础可访问性 3/3。
- 截图存于 Git 忽略目录 `.storyos-tmp/ui-qa/r12/`；隔离改造只改 Console 和该验收文档，不覆盖 `episodes/`、`media/`。
- 完成后必须在主分支干净且与集成分支有祖先关系时 `git merge --ff-only`，保留全部未跟踪作品文件。

## 下一步

对已审核素材构建专门的**本地受限只读媒体 API**，经映射表明确所属 Episode、Frame 和 approved 状态，再在浏览器中展示真实图片；在该接口完成前保持诚实的“无原图”。

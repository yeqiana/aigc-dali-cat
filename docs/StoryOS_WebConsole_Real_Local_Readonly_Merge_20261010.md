# StoryOS Web Console：真实本机数据与目标分支合并验收（2026-10-10）

## 合并范围
- 目标：`story-platform-v3-rever`。此前主分支已经包含 R1–R7（PR #26），本轮先在隔离 `integration/storyos-webconsole-real-merge-20261010` 合并 R8 变更，再接入本地真实只读数据。
- 四槽分工：本机文件状态只读后端、前端真实来源提示及安全启动器、API 隔离回归、真实 Chrome 联调和合并前检查。
- 所有合并与回归在独立 Worktree 完成；不会 checkout/reset/clean 用户主工作区，也不会修改任何 `episodes` 文件或数据库。

## 真实数据与边界
- `scripts/storyos_local_readonly_api.py` 只扫描指定主工作区 `episodes/**/meta/episode-state.json`，按文件真实 `current_state` 返回只读阶段。当前本机扫描得到 **20** 条有效记录。
- 原业务 Episode ID 可能跨作品重用，本地 API 用文件相对路径计算稳定定位符，保留原业务 ID；实测 **20/20** 定位符唯一。
- 来源 `local_workspace_episode_state_file`：真实磁盘证据，不是 MySQL 权威 Runtime。缺少 Worker/心跳/执行动作的地方必须为 `UNKNOWN` 或空值。
- 后端仅监听 loopback，允许 `GET /healthz`、`GET /api/v1/runtime/statuses`、`GET /api/v1/runtime/status`；其他请求拒绝，禁用跨域读取，不构建默认 Controllers，不连接 MySQL/Redis，不调用生图。
- 前端通过 Vite 同源代理使用私有 `STORYOS_PLATFORM_PROXY_TARGET`，不向浏览器开放数据库或 API 主机地址，也不修改已存在的 .env。

## 本机使用和测试
从目标分支合并后的 `web-console` 目录启动：

```powershell
npm run dev:local:real
```

访问 `http://127.0.0.1:3100/`；后台只读 API 默认 `127.0.0.1:19117`。Ctrl+C 终止。若需要选择其他真实工作区，设置 `STORYOS_LOCAL_DATA_ROOT`；仅在充分信任本机文件内容的情况下使用。

验收项目：
- Python `unittest discover -s tests/platform -p test_local_workspace_readonly.py -v`：重复业务 ID、阶段一致性、分页、无法推断的运行状态、只读 HTTP/禁止跨域与 POST。
- `npm run lint`、`npm run build`、既有 API 和监控等回归；
- `npm run test:local-real`（需已运行上述本机真实只读服务）验证真实状态数量、首页/监控来源、浏览器交互和未知心跳；
- 合并前比较主分支已跟踪脏状态与新增文件/未跟踪文件冲突，不执行清理。

## 后续限制
- 这不是直连 MySQL/Redis 的正式 Runtime E2E；不能据此判断在线 Worker、队列、调度器实际健康。
- 作品历史索引、Run/审图等旧快照在相应旧页面仍存在，已与真实只读阶段显示分层。后续要逐步以正式 Platform API 权威源替换它们，须先完成最小权限和只读连接审计。

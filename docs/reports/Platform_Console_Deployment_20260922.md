# Platform Console 运行态部署证据（2026-09-22）

## 结论

Platform API 与 Web Console 已通过同一 launcher 在当前用户会话中运行，Trace Explorer 可经 Web Console 同源代理查询真实 `TB_TRACE_SPAN` 数据。Windows 计划任务注册被系统以 `Access is denied` 拒绝，因此开机自启尚未完成，当前不能宣布完整的 Production Observability Ready。

## 实施内容

- Platform API：`127.0.0.1:8080`
- Web Console production preview：`127.0.0.1:3000`
- `/api` 与 `/healthz` 在 Vite dev/preview 中代理到 Platform API
- launcher 只读取既有 `STORYOS_MYSQL_*` 用户环境变量，不保存密码
- Event Authority 与 Trace Authority 均未修改；未执行 Event → Span 回填

## 运行态证据

- `/healthz`：`UP`
- `/api/v1/runtime/events?limit=3&offset=0`：返回 3 条真实 `TB_EVENT_LOG` 投影
- `/api/v1/traces?limit=20&offset=0`：返回 1 条真实持久化 Span
- Trace ID：`trace_c7d3e05ac142451bbf60fc01677fe142`
- Span ID：`span_8858b3c011064462a099c0b0e444edb8`
- Trace 状态：`SUCCESS`
- `http://127.0.0.1:3000/traces`：HTTP 200
- `http://127.0.0.1:3000/api/v1/traces?...`：同源代理返回真实 Trace

## 停启恢复

主动终止 API 子进程后，launcher fail-fast 清理两个子进程，3000/8080 监听数降为 0。重新启动 launcher 后，两端口恢复，Health、Trace List、Trace Get 均再次通过。

## 未完成项

1. `StoryOSPlatformConsole` 计划任务注册失败：Windows 返回 `0x80070005 Access is denied`。需要具备计划任务注册权限的终端重新执行部署命令。
2. 本轮未重启操作系统，只完成进程级受控停启恢复。
3. 本轮复验使用 2026-09-21 已持久化的真实 Agent Runtime Span；未擅自触发会修改 Episode 或消耗模型额度的生产 Workflow。

## 测试结果

- Console 定向测试：14 passed
- `tests/platform`：472 passed，3 个既有 `datetime.utcnow()` 弃用警告
- `tests/system`：1258 passed，1 skipped，2 failed
- 两个 System 失败均为 `runtime.preferred_runtime` 期望 `WORK`、实际 `CODEX`。运行测试期间工作区出现了不属于本轮的 `config/storyos.yaml` 修改和 `episodes/误入桃花源/` 新目录；本轮未覆盖或纳入这些并发变更。
- Web Console production build：通过（Vite 1703 modules transformed）

## Production Observability Ready 判定

**NOT READY（仅剩运行部署门禁）**：真实 Event、真实 Span、API、Web Trace Explorer 与进程级恢复均通过；开机自启和一次指定 Episode 的正常生产 Workflow Trace 尚未验收。

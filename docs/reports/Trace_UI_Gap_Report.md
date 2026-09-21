# Trace UI Gap Report

日期：2026-09-21

## 审计结果

Web Console 原先已有 `TraceExplorer` 和 `GET /api/v1/traces/{id}` 深链，但只有按 ID get，没有 list，也没有持久化 Span 的可见空态。

## 本次补齐

- 保留原 get API 与深链，不删除或改变其响应契约。
- 新增 `GET /api/v1/traces`，支持 `limit/offset/episode_id/trace_id`。
- Trace Explorer 增加 Recent Trace Spans 只读表，明确标注 `TB_TRACE_SPAN · READ ONLY`；点击行复用已有详情展示。
- 不把 Runtime Events 当作 Trace 列表，不从 `TB_EVENT_LOG` 生成 UI 假 Span。

## 视觉边界

按 `web-console/DESIGN.md` 与 `skills/storyos-ui-design/SKILL.md` 的 Extract/Build 约束实施：复用现有 token、紧凑数据行、等宽 ID、无新增大卡片/渐变/第二套组件体系。

# Checklist: Browser QA (Evidence-Based)

需要浏览器验收的任务，不得只声明“页面正常”，必须记录实际验证证据。

## 记录要素：
1. **Viewport**：
   - `1366 × 768`
   - `1440 × 900`
   - `1536 × 864`
   - `1920 × 1080`
2. **Tested States**：
   - `RUNNING` / `WAITING` / `RETRYING` / `BLOCKED` / `FAILED` / `COMPLETED`
3. **Critical Boundaries**：
   - Story 剧集名称很长 / Run ID 很长；
   - Queue = 0 与 Queue = 999 边界；
   - Worker 槽位 0/4 与 4/4 满载；
   - Heartbeat 正常 3s 与延迟 180s 疑似失联；
   - Frame 0/20 与 20/20；
   - 异常数量 = 0 与异常堆叠。
4. **Interaction & State Preservation**：
   - Filter / Search / Sort 触发无误；
   - Drawer 打开状态在自动刷新时保持展开；
   - Tab 切换不丢失上下文；
   - 危险操作（重新生成/跳过）触发二次确认模态；
   - 控制台无未捕获运行时报错，无异常失败网络请求。

## 标准输出范式：
```text
Browser Verification
✓ 1536×864 Production Monitor
✓ RUNNING / WAITING / RETRYING states verified
✓ BLOCKED requires manual-action indication
✓ Frame Drawer remains open during refresh
✓ stale heartbeat presentation
✓ Queue 0 / 999 boundary tested
✓ no new console error
✓ no failed unexpected network request
```

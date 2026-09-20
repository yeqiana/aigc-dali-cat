# Rule: Source of Truth

Skill 定义使用规则，不重复维护业务事实。

以下内容以项目代码 / Contract 为最终 Source of Truth：
- Status Enum (`/src/types.ts`)
- Stage Enum (`/src/types.ts`)
- Runtime Action
- API Schema
- Permission
- Design Token (`/src/index.css`)
- Route
- Feature Flag
- Runtime Config

Skill 可以规定：
- RUNNING 应使用 success/running semantic；
- RETRYING 必须展示 attempt；

但不得规定：
- `RUNNING = #22C55E`（具体颜色必须来自当前 Theme / Token）；
- 重试最大次数硬编码为固定 3 次（必须读取实际后端 Contract 中的 `maxAttempts`）。

如果 Skill 描述与代码 Contract 不一致：
以当前已确认的 Contract 为准，同时将 Skill 漂移记录为待治理问题。不得同时维护两套事实。

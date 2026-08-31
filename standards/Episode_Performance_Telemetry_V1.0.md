# Story OS V2.1｜Episode Performance Telemetry V1.0

`meta/episode-performance-ledger.json` 是运行遥测，不是 Story Authority，也不是 Release Gate。

自动记录：
- CREATIVE_STORY
- PREIMAGE_COMPILE
- VISUAL_LOCK
- VISUAL_LOCK_BASELINE_REVIEW
- PRODUCTION
- RELEASE
- image attempts / repairs / technical failures
- IDEA_LOCKED → ... → PUBLISH_READY state transitions
- TOTAL wall time

`reports/story-os-performance-summary.json` 汇总已完成 Episode 的 P50 / P90 / average。

注意：Stage wall time 与 image backend seconds 会重叠，不允许简单相加。

Telemetry 任何异常必须 fail-soft，不得阻塞 Story Lock、Visual Lock、Production、Release 或 PUBLISH_READY。

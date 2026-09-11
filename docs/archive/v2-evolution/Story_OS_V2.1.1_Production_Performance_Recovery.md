# Story OS V2.1.1 R3.1 Runtime Closure FULL

本版本针对 2026-08-31《停电夜蜕壳》性能事故完成 Runtime Closure。

核心原则：Story / Character / Frame Contract 等创作 Authority 不因性能优化被削弱；优化集中在 runtime authority boundary、故障隔离、并发依赖、可恢复性、可观测性和升级安全。

## 事故基准

- image_continue：18:37 → 22:30，233 分钟。
- 已记录图片 backend attempt resource time 约 1001 秒；资源时间可能重叠，不能与 stage wall 相加。
- 当时只有 4 个候选、0 approved、16 pending，仍停在 STORYBOARD_LOCKED。

## R3 Closure

- Visual Lock calibration 不再属于 immutable preproduction subset。
- Critic technical failure != content failure。
- Current Visual Lock attempt 绑定 + Circuit Breaker。
- bounded speculative <= 6，正式 Visual Lock validator 复用。
- narrative escalation 与 generation dependency 分离。
- executable fault-path replay；TARGET_BUDGET 与 measured wall-clock 严格分离。
- overlap-aware critical-path telemetry。
- package integrity + strict runtime chain + exact transaction rollback。
- mandatory regression gate + automatic rollback。

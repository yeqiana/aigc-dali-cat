# Story OS V3 Phase9 Runtime Canary Simulation Report

更新时间：

2026-09-10

项目：

D:/workspace/YeQianWorkSpace/yeqian/storyOS

分支：

story-platform-v3

---

## 1. 验证目标

Phase9 Runtime Staging Canary Simulation 用于验证 Runtime Operations 在灰度流量场景下的治理能力。

目标不是执行真实 Production Switch，而是把灰度链路真正驱动一遍：

- Canary Traffic Routing
- Promotion Decision
- Rollback Drill
- Migration Gate
- Production Switch Decision

2026-09-10 状态变化：本报告此前停在「真实 Canary Traffic: Pending」，阻塞原因是「需要 Runtime Staging 环境、真实 Worker 与流量入口」。P9.28 交付常驻 Runtime Worker 载体后，本批新增 scripts/phase9_canary_drill.py 完成真实执行，Pending 已解除。

---

## 2. Canary Runtime Components

涉及模块（全部调用既有公开 API，不复制判定逻辑）：

- platform/gateway/canary_runtime_gateway.py（sha256 bucket 分流）
- platform/gateway/canary_observability_metrics.py
- platform/gateway/canary_soak_window.py
- platform/gateway/canary_promotion_gate.py
- platform/gateway/canary_progressive_rollout.py
- platform/gateway/canary_auto_rollback.py（P8.5）
- platform/gateway/canary_promotion_evidence.py
- platform/gateway/canary_production_switch_decision.py

驱动脚本：

- scripts/phase9_canary_drill.py（2026-09-10 新增）

---

## 3. Simulation Flow

    V2 Runtime
        |
    Gateway（sha256 bucket）
        |
        +---- Canary Traffic
                  |
                  V
            V3 Runtime
                  |
            Metrics / Trace
                  |
            Promotion Gate / Soak Window
                  |
            Rollback Decision / Production Switch Decision

---

## 4. Validation Items

### Traffic Routing

- 流量比例控制（1 / 10 / 50 / 100）
- Canary target 选择
- Gateway 路由规则与粘性 bucket

### Promotion Decision

- Health 状态
- Latency 指标
- Error Rate
- Soak 样本量

### Rollback

- Failure detection
- Rollback trigger
- Gateway 回到 production_default

---

## 5. 真实执行证据

环境：

    Redis   127.0.0.1:6379（8.10.1，AOF，无密码）
    MySQL   121.89.82.216:9000 / story_os_runtime（8.0.46 / utf8mb4）
    探针    每次采样 = Redis ping + MySQL SELECT 1（只读，不写业务数据）
    故障注入 MySQL 指向被拒绝端口 127.0.0.1:1

命令：

    python scripts/phase9_canary_drill.py

一次真实执行：

    started_at   2026-09-10T14:59:00.678635
    finished_at  2026-09-10T15:03:46.588318（约 4m46s）
    episode_id=drill_canary_episode  stages=1,10,50,100
    requests_per_stage=1000  samples_per_stage=120
    steps=47  failed=0  退出码=0

### 5.1 真实分流（每阶段 1000 个确定性粘性 key）

| 目标比例 | 实测比例 | v3 / v2 | 路由 reason |
| --- | --- | --- | --- |
| 0（网关关闭） | 0.0% | 0 / 1000 | production_default |
| 1 | 1.3% | 13 / 987 | canary_bucket_match / canary_bucket_miss |
| 10 | 10.9% | 109 / 891 | canary_bucket_match / canary_bucket_miss |
| 50 | 48.8% | 488 / 512 | canary_bucket_match / canary_bucket_miss |
| 100 | 100.0% | 1000 / 0 | canary_full_traffic |

容差 ±2.0 个百分点，全部通过。晋级两轮（回滚前后各一轮）实测比例完全一致，说明分流对同一粘性 key 是确定性的。

### 5.2 粘性 bucket 单调超集

每个更高阶段都断言「上一阶段的 v3 key 集合是当前阶段的子集」：

    1 -> 10    13  子集于 109
    10 -> 50   109 子集于 488
    50 -> 100  488 子集于 1000

共 6 次断言（两轮晋级各 3 次）全部通过。这是真实 sha256 bucket 的性质，不是构造出来的。

### 5.3 探针健康与延迟

每个阶段 120 次真实探针，0 失败：

| 阶段 | 平均延迟 | 最大延迟 |
| --- | --- | --- |
| 1（第一轮） | 32.5 ms | 281.2 ms |
| 10（第一轮） | 34.7 ms | 283.7 ms |
| 50（第一轮） | 28.3 ms | 41.7 ms |
| 100（第一轮） | 47.6 ms | 587.9 ms |
| 1（第二轮） | 114.0 ms | 10149.4 ms |
| 10（第二轮） | 29.1 ms | 267.1 ms |
| 50（第二轮） | 29.2 ms | 271.2 ms |
| 100（第二轮） | 31.6 ms | 282.6 ms |

观察：第二轮 1% 阶段出现一次 10149 ms 的 WAN 抖动，平均延迟仍为 114 ms，未触发任何门禁。这类偶发抖动是跨机房 MySQL 的真实表现，已如实记录，不做平滑。

### 5.4 晋级门禁与渐进推进

四个阶段的 Promotion Gate 全部返回 PROMOTE（soak_passed），渐进推进在 1 / 10 / 50 返回 PROMOTE（stage_healthy），在 100 返回 COMPLETE（rollout_complete）。网关配置在 apply 前等于被评估阶段、apply 后等于决策的 next_percent，逐阶段核对通过。

### 5.5 回滚演练

探针切到故障实现（MySQL 指向 127.0.0.1:1）后：

    实测 error_rate=1.0（120/120 失败）
    平均延迟 2035.3 ms（被拒绝端口的连接尝试约 2s，不是瞬时失败）
    P8.5 回滚策略 -> ROLLBACK_TO_V2，reason=error_rate_exceeded
    P8.5 CanaryRollbackController 返回 V2_RUNTIME / production_default
    渐进推进控制器把网关置回 enabled=false / percent=0
    回滚后任一请求都命中 production_default

### 5.6 生产切换决策

    100% 阶段证据 -> SWITCH_TO_V3 / canary_production_ready / target_runtime=V3_RUNTIME
    50%  阶段证据 -> KEEP_CANARY / canary_not_completed（前置守卫按设计拦住）

---

## 6. Boundary（真与不真）

真实的部分：

- 分流走真实 sha256 bucket 代码，粘性 key 的单调超集可验证
- 每次采样是真实只读探针（Redis ping + MySQL SELECT 1），延迟是真实测量值
- 回滚由真实驱动异常触发，不是构造的失败指标
- 晋级 / 回滚 / 切换决策全部调用既有生产实现

仿真的部分：

- 请求流是确定性生成的粘性 key，不是真实用户流量；平台当前没有生产流量入口
- 「120 次采样」只代表一个观察窗样本，不等于线上 QPS 观测
- 分流容差 ±2.0 个百分点是固定 1000 key 样本的容差，不是统计置信区间

只读部分：

- 探针不写业务数据，不产生 event / trace / artifact 行

不做的事：

- 不做 V2 -> V3 的归属切换；本报告只产出决策证据
- 未接入真实 metrics 采集后端与告警通道

---

## 7. Conclusion

Phase9 Canary Simulation 从「代码契约验证」推进到「真实执行 + 证据」。

    代码契约验证     PASS
    真实 Canary 执行  Executed（47/47 步 0 失败，退出码 0）
    离线回归         tests/platform/test_phase9_canary_drill.py  14 例（全注入探针，真实控制面）

Production Ownership Switch 仍未执行，仍需真实环境验证。

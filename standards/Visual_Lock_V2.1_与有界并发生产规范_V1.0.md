# Visual Lock V2.1 与有界并发生产规范 V1.0

## Phase 5：四层 Visual Lock

Visual Lock 固定四个准入角色：

1. ordinary_baseline
2. worst_capture_condition
3. first_major_anomaly
4. high_impact_admission

正确执行顺序：

```text
Resolved Frame Contract PASS
→ baseline 先生成
→ worst / first anomaly / high impact 可并行
→ 统一 Visual Lock Critic
→ PASS
→ Batch
```

统一 Critic 同时判断：

- 母风格是否真实落地
- ordinary-life density
- available light
- unposed capture
- not cinematic
- causal imperfection
- environment physics
- capture credibility
- anomaly scale delivery
- scale reference fidelity

**异常大不是失败理由。**  
失败的是：异常明明要求 impact 4，实际像 impact 1；或者异常够大但整张图变成电影海报/概念图。

## Phase 6：有界并发

默认：

```text
max_parallel_image_workers = 3
```

并发仅用于真正耗时的 image backend。

Production Ledger 的所有 begin / success / tech-fail 写入由 Scheduler 主线程顺序执行，避免 JSON ledger 并发覆盖。

每个 image worker 自己拥有：

- 独立 TemporaryDirectory
- 独立 output
- 独立 log
- 独立 attempt id
- 独立 Frame Contract SHA

禁止扫描全局目录寻找“最新图片”。

## 自适应降速

- 正常：3
- 某波技术失败：降为 2
- 再失败：降为 1
- 连续稳定两波：逐级恢复
- 最大永远不超过 3

## Critical Path

优先级由 Frame Contract 计算：

- climax
- anomaly_amplified
- anomaly_reveal
- payoff
- high impact
- ordinary setup / transition

`escalation_from` 默认进入依赖图。

## Fail-soft

某帧技术失败：

- 记录 TECH_FAILED；
- 不消耗内容返修预算；
- 只阻塞依赖该帧的下游；
- 无关帧继续生成；
- Scheduler 完成当前可运行工作后返回 PARTIAL。

使用：

```text
image_scheduler.py retry-tech
image_scheduler.py run
```

继续技术重试。

## Repair Queue

内容审核失败后仍遵循“每帧普通内容返修最多一次”。

先按现有 Production Ledger 正式授权 repair，再：

```text
image_scheduler.py add <episode> --frame NN --kind repair --scope repair --prompt-file ...
image_scheduler.py run <episode>
```

技术失败和内容返修是两套预算，不能混用。

## 本阶段不做

Fast Frame Scout 仍属于 Phase 7。

Phase 5/6 不取消 Final Frame Semantic Critic。

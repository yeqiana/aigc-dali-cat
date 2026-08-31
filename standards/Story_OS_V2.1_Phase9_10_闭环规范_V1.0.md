# Story OS V2.1 Phase 9 + 10｜迁移、回归、可观测与发布数据闭环规范 V1.0

## Phase 9：Migration / Regression / Observability

### 1. Migration 默认只读

历史 Episode 不因为 Story OS 升级而被补造：

- Concept PASS
- Environment PASS
- Frame Contract PASS
- Visual Lock PASS
- Fast Scout PASS
- Snapshot PASS

旧 2.0.x / unversioned Episode 默认：

```text
LEGACY_COMPAT
→ KEEP_LEGACY_NO_BACKFILL
```

`migrate_v21.py activate` 只允许显式为 **已经是 V2.1** 的 Episode 开启当前 policy config，而且绝不生成 PASS evidence。

### 2. Regression Matrix

正式 V2.1 Closure 至少验证：

- 七阶段不可漂移；
- `episode-state.json` 仍是唯一 stage source；
- CODEX 在 PUBLISH_READY 完成，ZIP 非 stage gate；
- max3 + Production Ledger 单写者；
- Fast Scout 不是 final PASS；
- Snapshot 在 PUBLISH_READY 前；
- Delivery 只消费 verified Snapshot；
- Legacy no-backfill；
- 新 Episode template 带当前 policy；
- 发布后不得修改冻结 Release Manifest；
- 6h/24h/48h/7d 数据窗，48h 为 DATA_REVIEWED 最低门槛；
- 既有 Story regression；
- Workflow runner self-test。

### 3. Observability

`meta/workflow-observability.json` 只做诊断，不能推进 Episode state。

汇总：

- 慢步骤；
- scheduler wave；
- max observed parallel；
- ledger / queue status；
- tech/content/block failure taxonomy；
- Scout decision；
- Snapshot presence；
- post-publish checkpoint。

## Phase 10：Publish → Data Review → Next Story

### 4. Final Snapshot 发布后不能被事实回填破坏

**禁止**为了写 `published_at`、post_id、48h 数据去修改冻结后的 `release-manifest.json`。

发布事实写：

```text
meta/publish-event.json
```

数据写：

```text
meta/post-publish-metrics.json
meta/post-publish-review.json
meta/data-review-state.json
meta/next-story-learning.json
```

`validate_episode.py` 对 PUBLISHED / DATA_REVIEWED 优先读取这些 post-publish evidence，并保留旧 manifest 字段兼容。

### 5. 发布时间事实

`mark-published` 在真实发布后记录：

- published_at
- platform
- post_id（可选）
- post_url（可选）
- Final Candidate Snapshot SHA

通过机器门禁后推进唯一 `episode-state.json`：

```text
PUBLISH_READY → PUBLISHED
```

### 6. 数据窗口

支持：

```text
6h
24h
48h
7d
```

48h 是进入 `DATA_REVIEWED` 的最低必要 checkpoint；7d 可以在 DATA_REVIEWED 后继续补充复盘。

原始指标不强制平台字段全集，可按实际后台获得的数据记录：

- views
- likes
- comments
- shares
- saves / favorites
- followers_gained
- profile_visits
- completion_rate
- avg_view_duration_seconds
- 其他数值指标

系统只做账号内相对比较，不内置“平台万能阈值”。

### 7. Learning Packet

数据复盘生成：

```text
meta/next-story-learning.json
```

它是下一篇选题输入证据，不是创作权威。

禁止：

- 因一篇高野心内容数据差就降低 Concept Ambition；
- 因一篇高播放就机械复制同一机制；
- 用数据跳过 Story / Concept / Visual gates。

### 8. Account Learning Index

聚合最近已复盘 Episode：

```text
reports/account-learning-index.json
```

提供：

- 最近 Episode 指标；
- 账号内 median rates；
- top observed views / save / comment / share / completion；
- 对应 concept binding。

下一篇 Concept Ambition 前读取，但只作为 evidence。

# StoryOS《未交的答卷》PRODUCTION_PASSED → PUBLISH_READY 后半程慢归因（2026-09-30）

> 状态：**READ-ONLY FORENSIC ANALYSIS / 独立性能归因**
>
> 范围：只分析《未交的答卷》从 `PRODUCTION_PASSED` 到首次 `PUBLISH_READY` 的后半程，以及与这一阶段直接相关的 Review / Release / Telemetry 行为。
>
> 不包含：重新生产图片、修改 Episode Authority、修改 Gate、代码修复、配置切换。
>
> 关联前序分析：
>
> - `docs/Story_OS_本轮改造后暴露问题与运行慢归因_20260929.md`
> - `docs/Story_OS_视觉生产提速与全局双次生图上限落地方案_20260930.md`
>
> 前序文档已经把 Visual Lock / Production First Pass / Repair / Final Semantic 图片链拆到较深程度。本文件补齐之前没有完整分析的 **Episode 后半程 Release 链**。

---

# 1. Executive Summary

《未交的答卷》第一次真实进入 `PUBLISH_READY`：

```text
正式 Episode 启动
2026-09-29 13:38:11.776 +08:00

PUBLISH_READY
2026-09-30 17:19:17 +08:00

总墙钟
≈ 27h 41m 05s
```

其中：

```text
PRODUCTION_PASSED
2026-09-30 12:45:16 +08:00

→ PUBLISH_READY
2026-09-30 17:19:17 +08:00

后半程墙钟
≈ 4h 34m 01s
```

这 **4h34m 不是图片生成造成的**。

后半程主要慢在三类问题：

1. **Review Executor 太重**
   - Caption Review 本应只是“最多 5 张最终字幕图 + 5 条字幕”的窄任务；
   - 实际使用通用 Codex Agent，允许读取 Memory / START_HERE / SKILL / config / standards / repo；
   - 本次保留下来的 5 个 Caption Critic log 合计约 **1,929,229 input tokens**；
   - Release Critic 单次约 **935,495 input tokens**；
   - 仅这两类已观测 Review 合计约 **2,864,724 input tokens**。

2. **Review / Host Handoff 生命周期没有收干净**
   - Product Review request 可以先进入 `AWAITING_PRODUCT_REVIEW`；
   - 后面又改走 direct CODEX；
   - direct CODEX 路径产出了合法 Review，但没有同步关闭原 Product Review request/span；
   - 最终 `episode_performance.finalize()` 把遗留 RUNNING span 一律以 `CLOSED_AT_FINALIZE` 收口；
   - 于是大量“等待/悬挂”被写成了超长 Review / ACTIVE 时间。

3. **Caption 像素证据已经够了，但对应执行链没有及时短路**
   - 16:19 已存在直接用户字幕接受记录，且绑定当前字幕 SHA + 20 张当前图片 SHA；
   - 16:32 再次记录同一 current pair 的用户接受；
   - Release Gate 代码明确允许该 current user acceptance 解决特定的 `CAPTION_CORE_EVIDENCE_UNVERIFIED`；
   - 这意味着 current User Acceptance 可以满足/替代 Caption Pixel Review 的这一项证据要求，但**不能替代整个 Release Semantic Critic**；
   - pending Caption Review 应被 cancel / supersede / short-circuit；Release Semantic 仍需继续完成其余发布语义检查，只是不应再重新做已经被 current receipt 满足的字幕像素判断。

因此本轮后半程最重要的结论是：

> **慢点已经从 Image Provider 转移到 Review Orchestration、Runtime Handoff、Evidence Freshness 与 Telemetry Lifecycle。**
>
> 继续增加图片 Worker，无法解决这 4h34m。

---

# 2. 状态机真实时间线

来自当前 Episode Performance evidence：

| 状态 | 时间 | 与上一节点间隔 |
|---|---:|---:|
| Episode start | 09-29 13:38:11 | — |
| STORYBOARD_LOCKED | 09-29 14:47:07 | 1h08m55s |
| VISUAL_CALIBRATED | 09-29 18:59:46 | 4h12m39s |
| PRODUCTION_PASSED | 09-30 12:45:16 | 17h45m30s |
| **PUBLISH_READY** | **09-30 17:19:17** | **4h34m01s** |

整个 Episode：

```text
critical_path_seconds ≈ 99,667s
≈ 27h41m
```

前序《视觉生产提速》文档已经得到：

```text
图片链有效墙钟 ≈ 10h
成功 Generation 累计 provider elapsed ≈ 79m
```

所以剩余问题不是“为什么一张图生成两分钟”。

真正还没解释的是：

```text
为什么图片生产收口后，
Episode 还需要数小时才能进入 PUBLISH_READY；
以及为什么 Performance Ledger 又把大量跨夜 span 算成 ACTIVE。
```

---

# 3. PRODUCTION_PASSED → PUBLISH_READY 关键时间线

当前文件时间、Review provenance、Performance Ledger 可以还原：

| 时间 | 事件 | 观察 |
|---|---|---|
| 12:45:16 | PRODUCTION_PASSED | 后半程起点 |
| 13:23:49 | Caption audit round log | 前一轮字幕像素审查结束/落日志 |
| 14:33:27 | Caption chunk log | 重审 |
| 14:41:43 | Caption chunk log | 重审 |
| 14:46:04 | Caption chunk log | 重审 |
| 15:19:37 | `caption-image-audit.json` | 当前审计结果写入 |
| 15:22:03 | `subtitle-voice-review.json` | Voice Review |
| 15:22:45 | Release Semantic performance span/request 开始 | Review request 生命周期开始 |
| 15:51:24 | `publish-copy.md` | 发布文案完成 |
| 15:52:13 | `release-manifest.json` | Manifest 更新 |
| 15:57:16 | `text-audit.json` | Text Audit |
| 16:07:31 | 新 Caption critic log | 又一轮字幕像素 Review |
| **16:19:40** | **用户字幕接受 #1** | current caption/image SHA 绑定 |
| **16:21 左右** | Release Critic 真正开始模型执行 | 与 request start 相差约 58m |
| 16:30:11 | `release-semantic-review.json` | Critic 结果落盘 |
| **16:32:12** | **用户字幕接受 #2** | 同一 current SHA 集再次确认 |
| 16:34:07 | `frame-semantic-audit.json` | Evidence 收口 |
| 17:00:32 | `recommendation-fit.json` | Recommendation evidence |
| 17:11:26 | `story-dna-trace.json` | Story DNA evidence |
| 17:11:40 | `story-gates.json` | Gate 更新 |
| 17:13:01 | `final-candidate-snapshot.json` | Snapshot |
| 17:16:59 | `frame-scout-summary.json` | Scout evidence |
| **17:19:17** | **PUBLISH_READY** | 后半程结束 |

注意：

> 上述时间点存在并发和覆盖，不能把每一段间隔简单相加当成 CPU/模型工时。

但它足以证明：

- 后半程主要在 Review / Evidence / Gate；
- 不是 Image Generation；
- 多个 Review request 的“请求开始时间”与“模型真实开始时间”之间存在明显空窗；
- Review 结束后仍有几十分钟 Evidence/Gate 收口。

---

# 4. 根因一：Caption Review 的任务很窄，Executor 却是通用大 Agent

## 4.1 代码本来只要求审 5 张以内

`caption_image_audit.py`：

```text
CHUNK = 5
```

Prompt 明确要求：

```text
Review ONLY the supplied FINAL publish pixels
Do not re-review overall story quality,
character continuity, or visual style.
```

职责只有：

1. caption 是否被真实画面支持；
2. 字幕是否挡住语义关键物；
3. 必要时建议一个新的 y ratio。

这是一个非常窄的 Vision Judgment。

---

## 4.2 但真实 Agent 做了大量仓库探索

保留的 Caption Critic log 显示，Agent 会自行读取/搜索：

- Memory；
- `START_HERE.md`；
- `SKILL.md`；
- `config/storyos.yaml`；
- `config/index.yaml`；
- standards；
- 其他仓库上下文。

也就是说执行边界实际上是：

```text
5 images
+
caption prompt
+
整个 StoryOS 工作区可探索上下文
```

而不是：

```text
5 images
+
5 captions
+
极小的 frozen semantic rules
```

---

## 4.3 Token 证据

本 Episode 当前保留的 5 个 Caption Critic log：

| Log | input tokens | cached input | output |
|---|---:|---:|---:|
| caption-image-audit-v2-r1-001 | 227,636 | 197,888 | 1,841 |
| caption-image-audit-v2-002 | 356,751 | 318,720 | 3,000 |
| caption-image-audit-v2-003 | 492,653 | 379,904 | 3,645 |
| caption-image-audit-v2-004 | 306,909 | 243,328 | 2,445 |
| caption-image-audit-v2-001 | 545,280 | 483,584 | 4,446 |
| **合计** | **1,929,229** | **1,623,424** | **15,377** |

对于“检查最终字幕像素”的任务，这个输入规模过大。

缓存命中不能消除：

- Agent 规划；
- tool dispatch；
- repo search；
- context scheduling；
- reasoning；
- host lifecycle；
- model latency。

因此“cached 很高”不等于“这条链就便宜”。

---

# 5. 根因二：Caption Chunk 是串行的，不是并行的

当前 `caption_image_audit.ensure()`：

```python
for start in range(0, len(nonempty), CHUNK):
    chunk = nonempty[start:start + CHUNK]
    data = _run_chunk(...)
```

即：

```text
chunk 1
→ 等完成
→ chunk 2
→ 等完成
→ chunk 3
→ 等完成
→ chunk 4
```

标准 20 帧、全部需要 Vision 时：

```text
4 × 5-frame critic
```

最大并发不是 4，而是 **1**。

即使每个 Critic 只花 5～8 分钟，也自然变成：

```text
20～30+ 分钟
```

如果中间再发生：

- Host handoff；
- stale；
- layout repair；
- rerender；
- cycle 2；
- retry；

就会进一步放大。

这与图片 Generation 已经有多 Worker 并发形成明显反差：

> **图片生成已经流水化，字幕 Vision Review 仍是串行 Barrier。**

---

# 6. 根因三：Caption Evidence Freshness 导致多轮重审

`dirty_frames()` 对每帧检查：

```text
image_sha256
caption_sha256
passed
schema_version
local evidence freshness
```

任意一个变化：

```text
→ dirty
→ 重新进入 Caption Review
```

这个 fail-closed 设计本身是正确的。

问题是本次生产过程中同时发生了：

- 最终 publish 图片调整；
- 字幕文本调整；
- 字幕重新渲染；
- layout evidence 变化；
- Caption Review；
- 后续又直接用户接受。

于是同一后半程出现多份：

```text
caption-image-audit-v2-*.jsonl
```

当前可见：

- r1-001
- 002
- 003
- 004
- 001

说明不是“一次 20 帧审核后结束”，而是 freshness 改变后多轮重新进入。

结论不是取消 freshness：

> **Freshness 必须保留；要优化的是“改变一次字幕后，所有 downstream evidence 一次性 invalidation，然后一次性重新收口”，而不是边改边审。**

---

# 7. 根因四：用户已经接受当前字幕，重型 Review 没立即停止

Subtitle User Acceptance 历史：

```text
16:19:40
“不审核了，通过字幕审核，下一步”

16:32:12
“不审核了，通过字幕审核，下一步”
```

两份均绑定：

- 当前 `subtitles.yaml` SHA；
- 20 张 final publish rendered image SHA；
- current layout audit；
- caption content；
- rendered placement。

代码已经支持：

`caption_image_audit.user_acceptance_current(ep)`

并且 Release Semantic 验证明确允许：

```text
CAPTION_CORE_EVIDENCE_UNVERIFIED
+
current direct-user acceptance
→ Release Gate 可以合法通过
```

这是正确的 fail-closed exception。

但现在只有 **Verifier 知道用户接受可以 PASS**。

`caption_image_audit.ensure()` 本身没有在开头做：

```text
if user_acceptance_current:
    cancel/supersede pending review
    reuse user acceptance
    return PASS
```

因此会出现：

> Gate 已经有足够证据可以前进，但 Review Executor 仍可能继续跑。

这是典型的：

```text
decision authority 已经结束
execution lifecycle 没结束
```

---

# 8. 根因五：WORK Product Review 与 direct CODEX 混跑，留下悬挂 request/span

这是本次后半程最重要的代码级问题之一。

## 8.1 Product Review 生命周期

`product_review_adapter.prepare()` 会创建：

```text
AWAITING_PRODUCT_REVIEW
```

并启动性能 named span。

正常 Product Review 完成应该执行：

```text
mark_complete()
→ request.status = FINALIZED
→ safe_end_named_span(...)
```

---

## 8.2 但 direct CODEX Release Critic 路径不走 mark_complete

`release_preflight_review.cmd_run_release_critic()` direct CODEX 分支最后：

```python
return _finalize_release_review(ep, data, provenance)
```

它不会自动：

```python
product_review_adapter.mark_complete(...)
```

而 WORK Product Review finalize 路径才会：

```python
rc = _finalize_release_review(...)
if rc == 0:
    product_review_adapter.mark_complete(...)
```

因此如果流程发生：

```text
先 prepare WORK request
→ AWAITING_PRODUCT_REVIEW
→ 后来改走 direct CODEX
→ direct CODEX 产出最终 review
```

就可能出现：

```text
Evidence 已完成
但旧 WORK request 仍 AWAITING
Performance span 仍 RUNNING
```

这与本次真实 telemetry 完全吻合。

---

# 9. Release Semantic：Telemetry 说 116 分钟，模型实际上约 9 分钟

Performance Ledger：

```text
PRODUCT_REVIEW_RELEASE-SEMANTIC
15:22:45
→ 17:19:18
duration = 6993.419s
≈ 116.6m
status = CLOSED_AT_FINALIZE
```

但 `release-critic.jsonl` 的真实 Codex 运行时间戳：

```text
first model/runtime log ≈ 16:21:00
last model/runtime log  ≈ 16:30:11

≈ 9m11s
```

并且 Review provenance：

```text
reviewed_at = 16:30:11
```

所以这里至少有三段：

```text
15:22:45 → ~16:21
≈ 58m
request / orchestration / handoff window

~16:21 → 16:30:11
≈ 9m11s
real critic execution

16:30:11 → 17:19:18
≈ 49m
review 已落盘但旧 performance span 没关闭
```

这三段不能再合成一句：

> “Release Semantic 跑了 116 分钟。”

准确说法应为：

> **Release Semantic 的模型执行约 9 分钟；其 request 生命周期约 116 分钟，其中大量时间属于 handoff/wait 和 dangling telemetry。**

---

# 10. Release Critic 自身也严重过上下文化

虽然模型真实执行约 9 分钟，不是 116 分钟，但它仍然太重。

本次 `release-critic.jsonl`：

```text
input_tokens          = 935,495
cached_input_tokens   = 861,952
output_tokens         = 11,039
reasoning_output      = 6,890
command_execution     ≈ 20 次
```

Release Critic 本来的任务只有约 11 个最终发布语义检查。

代码 Prompt 甚至已经说明：

```text
Do not reopen every body image here
```

但实际仍使用：

```text
通用 Agent
+
repo root working directory
+
可执行 shell / 文件探索
```

于是 Critic 可以重新：

- 搜 standards；
- 搜 repo；
- 检查历史上下文；
- 执行大量命令。

这说明：

> **Prompt 说“不要探索”并不能形成真正的执行边界。**

需要的是 executor-level bounded input，不只是文字提醒。

---

# 11. Caption + Release 已观测 Review 输入接近 286 万 tokens

仅当前保留证据：

```text
Caption Critic input
1,929,229

Release Critic input
935,495

合计
2,864,724 input tokens
```

cached input：

```text
Caption cached
1,623,424

Release cached
861,952

合计
2,485,376 cached input tokens
```

这还没有计算：

- Subtitle Voice Review；
- Recommendation Fit；
- Story DNA；
- Frame Semantic；
- 其他中间 Review。

所以后半程的模型成本不是“发布审核问了几个问题”。

真实形态更接近：

> **多个通用 Agent 反复重新理解同一个 Episode / 同一个 StoryOS 仓库。**

这正是当前最应该消掉的重复工作。

---

# 12. 根因六：Final Candidate Snapshot 自己又会重跑完整 preflight

`final_candidate_snapshot.build_lock()` 不是简单做 SHA 清单。

它先执行 `preflight()`。

preflight 包含：

```text
frame_semantic_review.verify_episode
visual_final_freeze.verify
caption_image_audit.verify
fast_frame_scout.audit
text_audit check
release_evidence_errors
character master validation
```

然后 `build_lock()` 又：

- materialize story review；
- materialize visual profile review；
- materialize Production Ledger；
- 收集大量 evidence；
- hash delivery files。

更重要的是：

`final_candidate_snapshot.verify()`

full mode 又执行：

```python
current = build_lock(ep, write_evidence=False)
```

即：

> **build 后 verify 不是只验证保存的 snapshot 自身，而是重新 build 当前 lock，再做全量比对。**

这意味着：

```text
BUILD
→ full preflight

VERIFY
→ 又 full preflight
→ 又 rebuild lock
```

如果 Release Package 再调用：

```text
final_snapshot.verify(ep)
```

又会进入一次。

当前 `release_package.py` 确实在 package build 前调用：

```text
final_snapshot.verify(ep)
```

这类设计非常安全，但在 LOCAL 单 Episode 上会产生明显重复验证。

---

# 13. 根因七：Release Gate 的正确性检查被实现成多处重复扫描

当前几个入口都可能分别验证：

- Caption image；
- Final Freeze；
- Release Semantic；
- Governance；
- Frame Semantic；
- Fast Scout；
- Story DNA；
- Snapshot；
- Manifest SHA。

安全性目标没有问题。

问题是缺少：

```text
Operation-scoped Verified Release Evidence Snapshot
```

因此同一个 immutable SHA set 在一个最终收口 operation 里，会被不同模块重复读取、重复 hash、重复 verify。

这与前面已经修过的：

```text
next_action.derive
重复 MySQL Authority read
```

本质上是同一种问题：

> **安全规则是对的，但没有 request/operation scope 的共享结果。**

---

# 14. 根因八：Performance Telemetry 把悬挂 span 自动拉到 PUBLISH_READY

`episode_performance.finalize()`：

```python
_close_open_telemetry(d, ended)
```

对仍然：

```text
status = RUNNING
```

的 span：

```python
ended_at = finalization time
duration = finalization - started_at
status = CLOSED_AT_FINALIZE
```

这个设计适合“保证账本没有 open row”。

但不能把这些 duration 当执行时间。

本 Episode 当前典型：

```text
HOST_ACTION_CREATIVE_STORY
≈ 27.7h
CLOSED_AT_FINALIZE

HOST_ACTION_VISUAL_LOCK
≈ 26.25h
CLOSED_AT_FINALIZE

REVIEW_FULL_1
≈ 7.14h
CLOSED_AT_FINALIZE

PRODUCT_REVIEW_RELEASE-SEMANTIC
≈ 116.6m
CLOSED_AT_FINALIZE
```

它们都不是对应模型/代码真实连续执行这么久。

---

# 15. Execution Session 也存在同类放大

最后一个 `episode_runner` session：

```text
09-29 21:49
→
09-30 17:19

ACTIVE ≈ 70,191s
≈ 19h29m
```

这明显包含：

- 跨夜停顿；
- 人工处理；
- 外部 Review；
- 用户交互；
- Host handoff；
- Episode 不在 Python 热执行中的时间。

因此当前：

```text
runtime_active_seconds ≈ 77,341s
≈ 21.5h
```

不能解释为：

> StoryOS CPU / Python / Agent 真跑了 21.5 小时。

准确解释应该是：

> **Execution Session 生命周期没有被足够细地切换为 HOST_WAIT / USER_WAIT / IDLE，最终被 finalize 统一关闭。**

---

# 16. 为什么 W-105 做过“ACTIVE / HOST_WAIT 分离”，这里仍然失真

W-105 的方向是对的：

```text
ACTIVE
HOST_WAIT
USER_WAIT
IDLE
```

已经进入 telemetry。

但这次证明：

> **有状态枚举 ≠ 所有真实生命周期都已经正确打点。**

只要某个长期 runner session 没有在：

- handoff；
- user decision；
- external Review；
- overnight pause；
- pending product request；

这些边界及时 transition，就仍会形成：

```text
一个巨大的 ACTIVE 区间
```

所以 W-105 的代码能力已经存在，但真实 Episode instrumentation coverage 仍不完整。

---

# 17. 4h34m 不能简单归到一个模块

后半程存在大量 overlap。

例如 Release Semantic：

```text
15:22 request started
→ 16:21 model real start
```

中间同时完成：

- publish copy；
- release manifest；
- text audit；
- caption audit；
- user acceptance。

因此不能写：

```text
58m release wait
+
29m publish copy
+
...
```

否则会重复计算。

正确方法是：

> **Wall-clock critical path + resource lane 分开统计。**

建议至少拆：

```text
LOCAL_CPU
DB_IO
IMAGE_PROVIDER
VISION_MODEL
TEXT_MODEL
HOST_WAIT
USER_WAIT
QUEUE_WAIT
IDLE
EVIDENCE_REBUILD
```

---

# 18. 当前能确定的后半程浪费

## 18.1 可以直接确认

### A. General-agent over-context

Caption + Release 已观测 input：

```text
≈ 2.86M tokens
```

明显超过任务最小需要。

### B. Caption chunk serial barrier

最多 4 个 5-frame chunk 串行。

### C. 多轮 freshness rebuild

字幕/图片变化造成多个 caption audit round。

### D. User acceptance 没有成为 Caption execution cancellation signal

Verifier 可以用 current receipt 满足特定 Caption Pixel Evidence，但 pending Caption Review execution 仍可能存在。这里**不代表整个 Release Semantic Critic 可以取消**。

### E. Runtime handoff 留下 AWAITING request

WORK prepare 后切 direct CODEX 时，旧 request/span 可能不闭合。

### F. Snapshot full verify 重跑 build/preflight

同 SHA set 重复检查。

### G. Telemetry auto-close 造成执行时间膨胀

`CLOSED_AT_FINALIZE` duration 不能当真实执行。

---

## 18.2 当前不能强行下结论

以下区间目前没有足够细粒度 span，不应伪造归因：

```text
16:34 frame-semantic-audit
→ 17:00 recommendation-fit
≈ 26m

17:00 recommendation-fit
→ 17:11 story-dna-trace
≈ 11m
```

可能包含：

- next_action / Gate；
- Evidence rebuild；
- DB reads；
- Agent / host action；
- 人工触发间隔；
- command orchestration。

当前只能标：

```text
UNATTRIBUTED_ORCHESTRATION_GAP
```

而不能直接说“recommendation-fit 跑了 26 分钟”。

这也是新的 instrumentation gap。

---

# 19. 与 MySQL / SQLite 的关系

前序实测：

```text
next_action.derive

旧：
≈ 39～68s

operation-scoped cache 后：
≈ 5～7s
```

因此 MySQL remote read amplification 确实是问题，但已经显著缓解。

LOCAL SQLite 改造仍然有价值：

- 去掉网络 DB jitter；
- 简化 Authority；
- 减少部署复杂度；
- 降低大量小 read/write 的尾延迟。

但：

> **SQLite 不能把 4h34m Release 链自动变成 20 分钟。**

因为当前主要慢点已经是：

```text
Review Executor
+
Host Handoff
+
Evidence invalidation
+
重复 preflight
+
Telemetry lifecycle
```

---

# 20. P0 优化顺序

## P0-1：建立 Review Execution 的唯一生命周期 Owner

禁止同一个 frozen request 出现：

```text
WORK request AWAITING
+
direct CODEX 已完成
+
旧 request 仍 AWAITING
```

规则：

```text
same review_kind
+ same attempt
+ same frozen source fingerprint

只能有一个 active execution owner
```

发生 runtime takeover：

```text
WORK → CODEX
```

必须先：

```text
SUPERSEDE / TRANSFER old request
→ close old span
→ open new execution span
```

不得靠 Episode finalize 收尾。

---

# 21. P0-2：User Acceptance 必须进入 Scheduler / Executor Short-Circuit

当前：

```text
user acceptance
→ verifier knows PASS
```

应改成：

```text
user acceptance current
→ pending caption review obsolete
→ cancel/supersede request
→ close span
→ caption ensure returns REUSED_USER_ACCEPTANCE
→ next_action continues
```

只要：

- caption SHA；
- rendered image SHA；
- layout SHA；

完全 current。

任何一个 SHA 改变，接受自动 stale，恢复正常 Review。

边界必须明确：

```text
User Acceptance current
→ 只短路 CAPTION_PIXEL_REVIEW / 对应 Product Review request
→ 只满足 Release Semantic 中与当前字幕像素证据直接相关的要求
→ 不取消 RELEASE_SEMANTIC 本身
```

当前 Release Semantic 仍负责封面承接、前三帧连贯、高潮升级、payoff honesty、description consistency、caption 语言质量、真实群体/地点表达等其余检查。只有这些检查也存在 current、合法的独立 evidence 时才可复用，不能把“用户接受字幕”扩大解释成“用户接受整个 Release”。

---

# 22. P0-3：Caption 4 Chunk 并行，而不是串行

当前：

```text
chunk1 → chunk2 → chunk3 → chunk4
```

改：

```text
chunk1 ┐
chunk2 ├─ max_inflight=4
chunk3 ┤
chunk4 ┘
→ deterministic merge
```

每个 chunk：

- 只写 candidate；
- 无 Authority 权限；
- parent 验证 exact frame coverage；
- parent 单写者合并。

与 Final Semantic 4-shard 的模式一致。

---

# 23. P0-4：Caption Critic 改成真正 Frozen Review Package

不能只在 Prompt 写：

```text
Review ONLY ...
```

还要在执行层限制。

建议输入：

```text
CaptionReviewPackage
├── max 5 rendered images
├── exact 5 captions
├── image SHA
├── caption SHA
├── OCR hint
├── face-safe hint
├── allowed y-ratios
└── compact semantic evidence
```

禁止：

- Memory；
- repo-wide search；
- START_HERE；
- SKILL；
- config/index；
- unrelated standards；
- shell exploration。

目标：

```text
单 chunk input
从 20万～50万+
降到真正的 bounded package
```

---

# 24. P0-5：Release Critic 同样冻结输入

Release Critic 当前单次：

```text
935k input tokens
20 次左右 command execution
```

建议 Frozen Release Package：

```text
ReleaseReviewPackage
├── cover
├── body01-03
├── climax
├── payoff
├── captions digest
├── publish copy
├── propagation card
├── current caption audit result
├── current user acceptance result
├── current governance result
└── 11 checks rubric
```

Critic 无权重新探索仓库。

它只做：

```text
semantic judgment
```

不再做：

```text
repository research
```

---

# 25. P0-6：Final Snapshot 一个 operation 内只完整验证一次

目标：

```text
VerifiedReleaseContext
```

一次 operation：

```text
verify all current SHA
→ produce immutable verification digest
→ build snapshot
→ verify snapshot internal SHA
→ package consumes verified snapshot
```

而不是：

```text
build
→ full preflight

verify
→ full preflight again

package
→ snapshot full verify again
```

注意：

> 只能做 operation-scoped reuse。
>
> 任何 source SHA 改变立即失效。
>
> 不允许跨 Episode mutation 长缓存 Gate PASS。

---

# 26. P0-7：Telemetry 必须把 WAIT 和 EXECUTION 分开

Review 至少拆：

```text
REQUEST_PREPARED
AWAITING_HOST
EXECUTION_STARTED
EXECUTION_FINISHED
FINALIZATION_STARTED
FINALIZED
```

Performance 输出：

```text
queue_wait_seconds
host_wait_seconds
model_execution_seconds
finalization_seconds
```

禁止再只输出：

```text
PRODUCT_REVIEW_RELEASE-SEMANTIC = 6993s
```

因为这会把：

- 等宿主；
- 真模型；
- 已结束但 span 悬挂；

混成一个数字。

---

# 27. P0-8：CLOSED_AT_FINALIZE 不得进入 active execution KPI

`CLOSED_AT_FINALIZE` 应视为：

```text
LIFECYCLE_INCOMPLETE
```

其 elapsed：

- 可以保留做 incident evidence；
- 不得计入 active model/runtime execution；
- 不得直接计入效率 SLO。

建议：

```text
observed_wall_seconds
known_active_seconds
known_wait_seconds
unattributed_seconds
dangling_span_seconds
```

五个维度分别输出。

---

# 28. 建议的后半程目标

当前：

```text
PRODUCTION_PASSED → PUBLISH_READY
≈ 4h34m
```

第一阶段工程目标：

| 环节 | 当前观察 | 第一目标 |
|---|---:|---:|
| Caption Review | 多轮、串行、重上下文 | <= 10m |
| Subtitle Voice/Text | 分散执行 | <= 5m |
| Release Semantic | lifecycle 116m；真实 model ≈9m | <= 10m wall |
| Evidence / Snapshot | 多处重验 | <= 5m |
| Gate / transition | 分散收口 | <= 5m |
| **后半程总墙钟** | **≈4h34m** | **<=30～45m** |

成熟目标：

```text
无人工修改、Evidence 一次 current：
PRODUCTION_PASSED → PUBLISH_READY
≈ 15～25m
```

这个目标不要求降低任何 Gate。

它要求的是：

> **同一份 current evidence 不重复理解、不重复审核、不重复全量扫描。**

---

# 29. 对整个 Episode 的影响

前序图片链成熟目标：

```text
≈ 1～2h
```

本文件后半程成熟目标：

```text
≈ 15～25m
```

加上 Story / PREIMAGE / Visual Lock 的合理流水时间后，一个无人工长暂停的标准 20 图 LOCAL Episode，不应继续以：

```text
27h41m
```

作为正常生产基线。

当前更合理的工程方向是：

```text
第一阶段：
<= 3～4h 到 PUBLISH_READY

成熟阶段：
≈ 1.5～2.5h 到 PUBLISH_READY
```

这里是工程目标，不是已达成实测。

必须通过下一篇真实 Episode 再验证。

---

# 30. 最终归因

《未交的答卷》后半程慢，不是一个单点 Bug。

它是以下因素叠加：

```text
通用 Agent 过上下文化
+
Caption chunk 串行
+
Freshness 多轮失效
+
User Acceptance 未取消 pending execution
+
WORK / CODEX Runtime takeover 生命周期未收口
+
Snapshot / Preflight 重复验证
+
Gate evidence 分散生成
+
Telemetry dangling span
+
Execution Session 状态切换覆盖不完整
```

其中优先级最高的不是“再优化模型速度”，而是：

```text
1. Review Frozen Package
2. Review Lifecycle Single Owner
3. User Acceptance Short-Circuit
4. Caption Shard Parallelism
5. Operation-scoped Release Verification
6. Accurate WAIT / EXECUTION telemetry
```

---

# 31. 一句话结论

> **《未交的答卷》从 PRODUCTION_PASSED 到 PUBLISH_READY 花了 4h34m，但真正的 Release Critic 模型执行只有约 9 分钟；大量时间消耗在 Review 过度上下文化、串行分片、Host/Runtime handoff、重复 Evidence 验证，以及完成后未及时关闭的生命周期上。后半程优化重点应从“模型/图片速度”转向“Review 与 Release Orchestration”。**

---

# 32. 后续实施边界

本文件只做归因。

如果进入实施，建议独立拆为：

```text
Phase R0
Review Lifecycle / Telemetry correctness

Phase R1
Caption Review parallel + frozen package

Phase R2
Release Semantic frozen package

Phase R3
Operation-scoped VerifiedReleaseContext

Phase R4
真实新 Episode benchmark
```

验收必须使用新 Episode 的真实生产数据，不允许用本 Episode 的历史 timestamp 反向修改成“优化后数据”。

---

# 33. 第二层深挖：真正的根因不是 Review 函数，而是控制面粒度

前 1～32 节回答的是“哪些 Review / Evidence / Telemetry 行为造成了 4h34m”。

继续向下一层追代码后，更根本的结论是：

> **StoryOS 当前 Release 后半程的执行粒度太粗。名义上已经有 Runtime DAG、Node Scheduler、Resource Manager，但真实生产仍然把 Release 当成一个大型串行复合步骤。上层调度器看不见内部可以并行的工作，因此无法精确调度、取消、复用和恢复。**

这不是单个函数优化能彻底解决的问题。

## 33.1 设计契约比真实 Runtime DAG 更细，但执行层没有吃进去

runtimes/workflow-contract.json 已经把：

~~~text
TEXT_RELEASE
FINAL_CANDIDATE_SNAPSHOT
PUBLISH_READY_GATE
~~~

定义成不同工作，其中 TEXT_RELEASE.parallelizable=true。

但真实 runtimes/runtime-dag.json 又把它们压成一个：

~~~text
RELEASE
├── TEXT_RELEASE
├── FINAL_CANDIDATE_SNAPSHOT
└── PUBLISH_READY_GATE
~~~

所以设计层已经细化，执行层又重新粗化。这属于 Runtime Contract 与 Executable DAG 的粒度漂移。

## 33.2 当前顶层 DAG 实际仍是一条 6 节点串行链

~~~text
INCREMENTAL_PLAN
→ CREATIVE_STORY
→ PREIMAGE_COMPILE
→ VISUAL_LOCK
→ PRODUCTION
→ RELEASE
~~~

runtime_node_registry.runtime_step_nodes() 只有 PRODUCTION 得到特殊 image_managed policy。

其余顶层 Step 默认都是：

~~~text
mode = serial
parallel_safe = false
resource_class = text
max_concurrency = 1
~~~

因此 Scheduler 的并发能力对 Release 基本没有发挥作用。

## 33.3 Review Resource Capacity = 1 是“拆 DAG 后的潜在限制”，不是当前 Caption 串行的直接原因

runtime_dag.production_scheduler_resources() 当前确实暴露：

~~~text
text: 1
review: 1
preimage: N
authority: N
derived: N
image: 5
~~~

但必须区分两层事实：

1. **当前 Caption Review 串行的直接原因**是 `caption_image_audit.ensure()` 里的同步 `for ... _run_chunk()`；
2. 当前 Caption / Release Critic 很多仍藏在 RELEASE / adapter 内部，并没有作为独立顶层 `review` node 进入 Runtime Scheduler，因此不能把现有 4h34m 直接归因于 `review: 1`。

所以 `review: 1` 的准确含义是：

> **未来把 Caption / Voice / Release Review 真正拆成 Scheduler 节点后，如果仍保留 review capacity=1，那么新 DAG 仍会被资源池重新串行化。**

它是后续并行化必须同步处理的资源配置约束，而不是当前 Caption 串行的直接证据。

## 33.4 Scheduler 即使返回多个 dispatch，Runtime DAG 当前也只执行第一个

runtime_scheduler.schedule() 支持返回多个 dispatch 节点。

但 runtime_dag._execute() 当前实际取：

~~~python
s = step_by_id[wave["dispatch"][0]["node_id"]]
~~~

所以：

> Scheduler 有并行规划能力，不等于 Runtime DAG 已有顶层并行执行能力。

后续只把某个节点标记 parallel_safe 仍然不够；执行器还需要真正执行一个 wave 的多个节点，再 deterministic fan-in。

---

# 34. RELEASE 目前是“Agent 里面再编排一套流程”

scoped_codex_worker.py 对 RELEASE Worker 的指令要求它自己完成：

- captions；
- publish copy；
- subtitle placement；
- text audit；
- subtitle voice review；
- release/compliance checks；
- Final Candidate Snapshot build + verify；
- delegated release approval；
- transition 到 PUBLISH_READY。

这意味着 RELEASE 不是一个单一模型判断，而是：

> **让一个通用 Agent 自己当小型 Orchestrator。**

实际控制流近似：

~~~text
Runtime DAG
  ↓
RELEASE Scoped Agent
  ↓
deterministic tools
  ↓
Caption / Release Critic
  ↓
Evidence
~~~

这属于 Agent-inside-Agent orchestration。

上层 Scheduler 无法看到 Agent 内部哪些工作可并行、哪些已经完成、哪些应该取消。

---

# 35. Parent Runtime 与 RELEASE Agent 存在“双控制器”

RELEASE Agent 被要求自己：

~~~text
完成 release checks
build+verify snapshot
transition PUBLISH_READY
~~~

但 RELEASE Worker 返回 rc=0 后，Parent Runtime 又执行：

~~~text
run_release_preflight_recovery()
→ validate_target(PUBLISH_READY)
~~~

也就是说实际职责是：

~~~text
Child RELEASE Agent：尝试完整收口一次
Parent Runtime：再确定性收口一次
~~~

Parent 的 fail-closed 验证是必要的。

问题在于 Child 不应该同时拥有“流程编排 + deterministic closure”的责任。

更合理的是：

~~~text
Machine Controller
唯一拥有 Release DAG

Agent
只负责不可确定的创作 / 语义判断节点
~~~

这可以直接减少重复调用和 ownership 模糊。

---

# 36. Host Wait / Resume 会把控制面从 DAG 顶部重新走一遍

每次调用 runtime_dag.execute() 都会重新：

~~~python
completed_nodes = set()
~~~

也就是本次内存调度状态从零开始。

即使 Episode 当前已经是 PRODUCTION_PASSED，仍会重新经过：

~~~text
INCREMENTAL_PLAN
CREATIVE_STORY
PREIMAGE_COMPILE
VISUAL_LOCK
PRODUCTION
RELEASE
~~~

前面的内容不会重新生成，但并不是零成本。

对于已经达到 target_state 的节点，runtime_dag 会重新执行 validate_target()。

而一次 validate_target() 包含：

~~~text
validate_episode
machine_gate
evidence_gate
~~~

因此 Release 阶段每发生一次 Host Review stop/resume，都可能顺带重新验证 STORYBOARD_LOCKED、VISUAL_CALIBRATED、PRODUCTION_PASSED。

这就是一种“内容没重做，但控制面重新扫全场”的放大器。

---

# 37. PUBLISH_READY 本身还可能连续做 2～3 次完整验证

当前代码路径至少存在三处：

1. RELEASE Step 成功后的 postcondition：validate_target(PUBLISH_READY)；
2. 如果使用 --until PUBLISH_READY，stop_target_reached() 再调用一次 validate_target(PUBLISH_READY)；
3. Resident episode_runner 看到终态后，再调用 runtime_dag.validate_target(PUBLISH_READY)。

因此同一 source SHA set 在没有变化的情况下，有机会连续做 2～3 次：

~~~text
validate_episode
+
machine_gate
+
evidence_gate
~~~

这不是安全规则太多，而是：

> **同一个安全结论缺少 operation-scoped reuse。**

但目前只证明了“存在重复 full validate 的代码路径”，**尚未量化这 2～3 次验证各自占了多少墙钟**。实施优先级应先补 timing/trace，再决定它是 P0 热点还是 P1/P2 优化；不能仅凭调用次数就把它当成本次 4h34m 的主要耗时。

这与此前 next_action 因同一 operation 重复 MySQL Authority read 而从 5～7 秒膨胀到 40 秒量级，本质上是同类问题。

---

# 38. Evidence Freshness 当前是“懒失效”，不是主动依赖失效

当前安全机制主要是：

~~~text
旧 Evidence 文件继续存在
↓
消费者读取
↓
重新计算当前 SHA
↓
发现 mismatch
↓
FAIL / rebuild
~~~

Fail-closed 原则本身是正确的。

但当前没有找到 Release 级的集中式 Evidence Dependency Graph。

字幕一改，并不会立即得到一个统一 dirty set，例如：

~~~text
subtitle source changed

DIRTY:
- subtitle layout
- rendered subtitle pixels
- caption audit
- subtitle user acceptance
- subtitle voice review
- text audit
- release semantic
- final snapshot
- release package
~~~

而是各模块以后各自发现“我 stale 了”。

结果就容易变成：

~~~text
跑到 stale A
→ 修 A
→ 继续
→ 跑到 stale B
→ 修 B
→ 继续
→ 跑到 stale C
~~~

即“串行发现依赖”。

注意：这里不建议 subtitle_layout.py 去直接删除一堆下游文件。

应该由一个独立 dependency calculator 根据 fingerprint 计算 current / dirty / blocked / ready。

---

# 39. 建议引入 ReleaseVerificationFingerprint，而不是缓存一个裸 PASS

这里必须比单纯文件 SHA 更严格。建议只做轻量机器派生，不引入第二套 Authority，但 fingerprint 必须覆盖**所有能改变 Gate 结论的文件事实 + Authority 事实 + Approval/Policy 事实**：

~~~text
ReleaseVerificationFingerprint

# 文件 / 发布输入
story_sha
storyboard_sha
approved_base_image_set_sha
caption_source_sha
subtitle_layout_sha
rendered_publish_image_set_sha
publish_copy_sha
propagation_sha
release_manifest_sha
publish_compliance_sha
story_gates_relevant_subset_sha
account_registry_sha
governance_config_sha
contract_or_policy_version

# 当前正式 Authority / DB evidence
episode_state_authority_id_or_sha
state_version
production_ledger_authority_sha_or_version
frame_review_db_evidence_digest
story_review_authority_sha_or_version
visual_profile_review_authority_sha_or_version
runtime_evidence_digest

# Approval / receipt
direct_user_acceptance_receipt_sha
release_approval_receipt_sha
delegated_approval_receipt_sha_if_used
~~~

字段可以按现有 Repository 能力落成“SHA / version / deterministic digest”，不要求新增一个总 Authority 表。

核心规则：

> **VerifiedReleaseContext 不是“刚才 PASS 过所以继续用”，而是“刚才 PASS 过，并且所有影响该 PASS 的 Authority/Fingerprint 到消费/commit 前仍完全一致”。**

每个 Release Node 声明消费哪些 key。

例如：

~~~text
TEXT_AUDIT
← caption_source_sha

SUBTITLE_LAYOUT
← caption_source_sha + approved_base_image_set_sha

CAPTION_PIXEL_REVIEW
← caption_source_sha
 + rendered_publish_image_set_sha
 + subtitle_layout_sha

SUBTITLE_VOICE_REVIEW
← caption_source_sha + voice_contract_sha

RECENT5
← story_fingerprint_sha + account_registry_sha

RELEASE_SEMANTIC
← rendered_publish_image_set_sha
 + caption_source_sha
 + publish_copy_sha
 + propagation_sha
 + caption evidence fingerprint

FINAL_SNAPSHOT
← all verified final release fingerprints
~~~

输入一变：

~~~text
一次 recompute
→ 一次得到完整 dirty set
~~~

不再等每个下游模块逐个报错。

此外必须有 **commit-time freshness fence**：

```text
build VerifiedReleaseContext
→ 执行 Snapshot / Package 等确定性工作
→ transition / authority commit 前重新读取当前 fingerprint
→ exact match 才允许消费 PASS
→ 任一字段变化则 context 立即 STALE，fail closed / recompute
```

否则 DB Authority、Approval Receipt 或 policy 在缓存后变化，会产生 stale PASS。

---

# 40. User Acceptance 应升级为“Caption 调度事件”，但绝不能替代整个 Release Semantic

当前 User Acceptance 可以作为 current、SHA-bound 的 Caption Pixel Evidence。它应从单纯 verifier 条件升级为控制面事件：

~~~text
USER_ACCEPTANCE_COMMITTED
↓
验证 caption SHA + rendered image set SHA + layout evidence current
↓
dependency graph recompute
↓
CAPTION_PIXEL_REVIEW = SATISFIED_BY_USER_RECEIPT
↓
对应 Caption AWAITING request → SUPERSEDED/CANCELLED
↓
释放对应 Caption Review execution / span / resource
↓
RELEASE_SEMANTIC 可以继续
~~~

**这里的 `RELEASE_SEMANTIC 可以继续` 不等于 `RELEASE_SEMANTIC 可以跳过`。**

当前 Release Semantic Critic 仍有 11 类发布语义检查。User Acceptance 只允许处理与 current caption/pixel evidence 相关的特定不确定性；封面承接、前三帧连贯、高潮升级、payoff honesty、description consistency、caption conversational quality、真实群体/地点表达等其余检查仍必须由 current Release Semantic Evidence 满足。

所以用户说“不审核字幕了，通过，下一步”时，Scheduler 应立即停止**Caption Pixel Review**，而不是停止整个 Release Review。

---

# 41. Provisional Release 当前是一个“孤儿优化”

runtime-dag.json 专门支持：

~~~text
provisional_release_parallel = true
~~~

会在 CREATIVE_STORY 后异步生成：

~~~text
meta/runtime/provisional-release.json
~~~

理论上是想利用图片生产时间，提前准备 Release 文案。

但本轮全仓引用扫描显示，这个正式产物除了：

- provisional_release.py 自身；
- episode_storage_policy.py；

没有生产消费者。

Final RELEASE 不读取它。

Final Snapshot 不读取它。

Release Preflight 不读取它。

所以当前逻辑近似：

~~~text
提前生成一份草稿
↓
没人消费
↓
Final Release 仍重新生成
~~~

本 Episode 当前没有保留下来的 provisional-release.json，因此不能把具体分钟数硬算进 4h34m。

从当前代码引用关系看，它属于**确定存在的“无正式生产消费者 speculative work 风险”**；但本 Episode 没有保留下来可量化的 provisional artifact / timing，因此不能据此声称它实际拖慢了本次 4h34m。

如果在 local CODEX 路径真的执行，它还可能与其他任务竞争：

- Codex runtime；
- subscription / API concurrency；
- CPU / IO；
- context cache。

合理处理只有两种：

1. Final Release 真正消费并校验这份 draft；
2. 没有正式 consumer 前关闭这条 speculative lane。

---

# 42. Recent-5 也存在跨阶段重复 Ownership

runtime-dag.json 中：

~~~text
CREATIVE_STORY covers RECENT5_SEMANTIC
~~~

Recent-5 的业务含义本来就是 Story Lock 前的原创性 / 机制相似度检查。

但 Release 的 cmd_prepare_auto() 第一件事又是：

~~~python
build_recent5(...)
~~~

而不是先：

~~~python
verify_recent5_evidence(...)
~~~

所以同一规则同时被：

~~~text
Story Creation
+
Release Preflight
~~~

拥有。

这里要区分两层：

- `build_recent5()` 会重新构建/写入 Recent-5 聚合结果；
- 其中 Semantic Review 走 `ensure_review()`，如果现有 review 对当前 fingerprint + registry + history 仍合法，会直接复用，并不会必然重新跑一次 Semantic Critic。

所以准确结论不是“Release 又完整重审了一次 Recent-5”，而是：

> **Story Creation 与 Release Preflight 对 Recent-5 存在 ownership 重叠，并存在重复聚合/验证计算；Semantic Critic 本身在 evidence current 时已有复用能力。**

Release 更合理的入口仍应优先：

~~~text
verify current aggregate + semantic evidence
↓
只有 fingerprint / registry / history stale
才 rebuild / rerun required part
~~~

这项目前属于架构整洁度与潜在重复计算问题，尚无证据证明它是本次 4h34m 的主要耗时。

---

# 43. Release 黑盒混合了三种性质完全不同的工作

当前 RELEASE 同时混合：

### A. Creative / Judgment

- captions 文案；
- publish copy；
- subtitle voice；
- release semantic。

### B. Deterministic Transformation

- subtitle render；
- hash；
- compliance structure；
- manifest；
- snapshot build；
- package lock。

### C. Verification / Authority

- text audit；
- caption verify；
- release verify；
- machine gate；
- evidence gate；
- transition。

于是一个 scoped Agent 既：

~~~text
创作
+ 跑工具
+ 调 Review
+ 判断结束
~~~

而 Parent Runtime 又必须重做 C 类验证。

这是重复工作的结构性来源。

---

# 44. 推荐的真正 Release DAG

不需要再造一个重框架，只需要把现有 RELEASE 黑盒拆成机器可见节点：

~~~text
PRODUCTION_PASSED
      │
      ├── RELEASE_SOURCE_FINGERPRINT        [machine]
      │
      ├── RECENT5_VERIFY_OR_REFRESH         [machine / critic only if stale]
      │
      ├── COMPLIANCE_PREP                   [machine]
      │
      ├── CAPTION_AUTHOR                    [text worker]
      │
      └── PUBLISH_COPY_AUTHOR               [text worker]
               │
               ▼
      SUBTITLE_RENDER                       [machine]
               │
        ┌──────┼──────────┐
        ▼      ▼          ▼
   TEXT_AUDIT  VOICE      CAPTION_PIXEL_SHARDS
   [machine]   REVIEW     [vision x4]
              [text]
        └──────┬──────────┘
               │
               ▼
      RELEASE_SEMANTIC                     [bounded critic]
               │
               ▼
      VERIFIED_RELEASE_CONTEXT             [machine]
               │
               ▼
      FINAL_CANDIDATE_SNAPSHOT             [machine]
               │
               ▼
      PUBLISH_READY_GATE                   [machine, single full pass]
               │
               ▼
           PUBLISH_READY
~~~

并行只发生在：

- 输入已冻结；
- 输出互不写同一 Authority；
- 没有依赖关系；

的节点之间。

不是“并发越多越好”。

## 44.1 并行前必须先冻结 Node 的 read-set / write-set / Authority Owner

Release DAG 一旦并行，最危险的不是“跑不快”，而是多个 Worker 同时写同一份正式 Evidence / Authority。

实施前每个 Node 至少声明：

| Node | 主要 Read Set | Worker Output | 正式写入/Authority Owner |
|---|---|---|---|
| CAPTION_AUTHOR | Story / release inputs | caption candidate | Parent single-writer commit captions |
| PUBLISH_COPY_AUTHOR | Story / release inputs | publish-copy candidate | Parent single-writer commit |
| TEXT_AUDIT | committed captions | audit candidate/result | deterministic audit writer |
| CAPTION_PIXEL_SHARD_1..N | frozen rendered pixels + captions | shard candidate | **不得**直接写总 `caption-image-audit` |
| CAPTION_PIXEL_FANIN | exact shard candidates | merged audit | Parent single writer |
| SUBTITLE_VOICE_REVIEW | frozen caption package | review candidate | review finalizer single writer |
| RELEASE_SEMANTIC | frozen ReleaseReviewPackage | critic candidate | release-review finalizer single writer |
| VERIFIED_RELEASE_CONTEXT | current files + Authority digests | derived context | 非 Authority，只读快照 |
| FINAL_CANDIDATE_SNAPSHOT | verified context | snapshot | snapshot writer |
| PUBLISH_READY_GATE | verified context + current Authority | Gate decision | Gate 本身不写 creative evidence |
| PUBLISH_READY_TRANSITION | PASS gate + expected state/version | transition request | **Episode State Authority 唯一 writer / CAS** |

硬规则：

```text
parallel worker = candidate-only
fan-in / finalize / authority transition = deterministic single writer
```

不得出现 4 个 Caption shard 并发修改同一个 `caption-image-audit.json`，也不得让多个 Review/Transformation 节点并发修改 `story-gates.json` 或 Episode State。

---

# 45. Resume 应从未完成 Release Node 继续，而不是从宏观 DAG 顶部重新证明一遍

建议每个 Runtime Node 持久化：

~~~text
node_id
input_fingerprint
status
output_fingerprint
attempt
execution_owner
~~~

Resume：

~~~text
读取当前 fingerprints
↓
计算 READY / DIRTY / AWAITING
↓
只继续这些节点
~~~

而不是：

~~~text
从 INCREMENTAL_PLAN 开始
→ 再证明前面每个已达阶段仍然成立
~~~

Canonical Episode State 仍然保持现有阶段状态。

这些只是 Runtime Node execution facts，不创建第二套业务状态机。

但“从未完成 Node 继续”必须有严格前提：

```text
saved input_fingerprint == current input_fingerprint
AND
所有依赖 Authority version/digest 仍一致
AND
上游 output_fingerprint 仍 current
```

只有满足以上条件才能 REUSE 已完成 Node。任何 Story / Caption / Rendered Pixels / Ledger / Review Authority / Approval / Policy 变化，都必须把受影响节点标为 DIRTY，并沿依赖图向下失效。

因此目标不是“Resume 后少验证”，而是“**用 deterministic fingerprint 证明无需重复验证**”。不能为了提速跳过 fail-closed freshness。

---

# 46. 完整 Gate 应只在两个明确边界跑

建议：

### 边界一：真正阶段 Transition 前

~~~text
PRODUCTION_PASSED → PUBLISH_READY
~~~

完整跑一次：

~~~text
validate_episode
machine_gate
evidence_gate
~~~

### 边界二：外部独立验收 / 显式 verify

比如 CLI validate、CI、人工审计。

同一 operation 内的：

- Snapshot build；
- Snapshot internal verify；
- Package；
- Runner completion；

可以消费同一个 VerifiedReleaseContext，**但每个真正 Authority commit / Transition 前必须重新比较 `context.fingerprint == current_fingerprint`**。

只允许：

```text
同一 immutable input/Authority set
→ reuse full-gate result
```

不允许：

```text
曾经 PASS
→ 不管 Authority / Approval / Policy 是否变化都继续复用
```

这样才能在不降低 Gate 安全性的前提下避免重复 full validate。

---

# 47. 第二层根因后的优先级应该重新排序

前一版 R0～R4 继续有效，但现在建议进一步调整：

### R0 — Control Plane Correctness

- Review request Single Owner；
- runtime takeover 必须 transfer / supersede；
- User Acceptance 只触发对应 Caption Pixel Review cancellation/supersede，不取消整个 Release Semantic；
- dangling span；
- WAIT / ACTIVE 正确打点。

### R0.5 — Resume / Gate Revalidation 去放大

- Resume 对 fingerprint 完全 current 的已完成 Node 直接 reuse；发生 Authority/source mutation 必须沿依赖图失效；
- 同一 operation 的 Gate 结果按完整 Authority/Fingerprint scoped reuse，并在 commit 前 freshness recheck；
- 先补 PUBLISH_READY validate timing，再消除同一 immutable source set 上可证明重复的 full validate。

### R1 — Release DAG Decomposition

先把 RELEASE scoped_model 黑盒拆开。

这是后面真正并行的前提。

### R2 — Bounded Review Executors

- Caption Frozen Package；
- Release Frozen Package；
- Voice Review Frozen Package。

### R3 — Release Dependency / Dirty Graph

一次 source mutation 立即得到完整 dirty set。

### R4 — Parallel Review Lane

- Caption shard 并行；
- 先把 Review 暴露为 Scheduler node，再按真实资源调整 review capacity（当前 `review=1` 不是 Caption 串行的直接原因）；
- candidate-only worker + deterministic single-writer fan-in。

### R5 — Provisional Release Cleanup

二选一：

- 正式消费；
- 删除无消费者 speculative work。

### R6 — 新 Episode Benchmark

只用新的真实生产 telemetry 验证。

---

# 48. 第二层结论

当前 StoryOS 的并发成熟度其实很不均衡：

| 区域 | 当前状态 |
|---|---|
| PREIMAGE | 已有 4-worker fan-out |
| Image Generation | 已有 max 5 并发 |
| Repair Images | 已进入并行 lane |
| Derived /部分 Fast Path | 已有并发能力 |
| Caption Review | 串行 chunk |
| General Review | 多数仍藏在大步骤/adapter 内；拆成 Scheduler node 后还会受 review capacity=1 限制 |
| Release | 一个大型 serial scoped model |
| Release Resume | 从宏观 DAG 顶部重走 |
| Final Gate | 同 SHA 可能重复 full validate |

所以更准确地说：

> **StoryOS 前半程已经逐渐变成 Scheduler 驱动，后半程仍然是 Agent Supervisor 驱动。**

第一层结论是：

> Review / Release Orchestration 慢。

第二层结论是：

> **因为 StoryOS 的 Release 还没有真正平台化。它仍然把一个通用 Agent 当作 Release 流程控制器，而 Runtime DAG 只看得到一个 RELEASE 黑盒。**

只要这个结构不改：

- 更快模型；
- SQLite；
- 更多 Worker；
- Caption 并行；
- 更多 cache；

都会有收益，但只能局部提速。

真正让后半程从小时级稳定降到分钟级，需要：

> **把 Release 的流程控制权从大 Agent 收回 Machine Scheduler，让 Agent 只做不可确定的创作和语义判断。**

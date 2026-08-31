# Story OS V2.1 Runtime Refactor P0.5 / P0.6 V1.0

## 目标

这次升级只优化工程执行层，不新增 Story Gate / QA Gate。

### P0.5
- Runtime DAG Step Protocol
- Scoped Codex Worker
- Step-level checkpoint / resume
- 已到达且 machine/evidence gate 仍 PASS 的阶段直接 REUSED

### P0.6
- workflow_runner 在新篇 Runtime Request `execution_mode=dag` 时改走 Runtime DAG
- 单个超长 Codex supervisor 被拆成四个有明确边界的昂贵步骤：
  1. CREATIVE_STORY
  2. VISUAL_LOCK
  3. PRODUCTION
  4. RELEASE

## Runtime DAG

```text
INCREMENTAL_PLAN
→ CREATIVE_STORY          -> STORYBOARD_LOCKED
→ VISUAL_LOCK             -> VISUAL_CALIBRATED
→ PRODUCTION              -> PRODUCTION_PASSED
→ RELEASE                 -> PUBLISH_READY
```

注意：Runtime DAG 是执行调度证据，**不是第二个 Episode Stage 系统**。最终权威仍然是：

```text
meta/episode-state.json
```

每个 Step 结束后必须重新跑：

```text
validate_episode.py
machine_gate.py
evidence_gate.py
```

Codex worker 返回 0 不能单独算 PASS。

## 中断恢复

每个 Step 写入：

```text
meta/runtime-dag-state.json
meta/runtime-checkpoint.json
meta/workflow-performance.json
```

恢复时：

```text
已到目标阶段
↓
machine/evidence 仍 PASS
↓
REUSED
```

否则只重跑当前 Step，不从故事开头重新开始。

这使得 Plus / Codex 额度中断后：

- Story Lock 后不重新编剧情
- Visual Lock 后不重新做四张准入
- Production 中已 PASS 帧继续复用
- Release 中断只恢复 Release

## Image Worker Pool

新增 `image_worker_pool.py`。

当前能力：

```text
复用 Scheduler Python 进程
复用 Python module import
不再为每帧额外启动 codex_subscription_image.py Python 子进程
```

但 Codex 图像调用本身仍是：

```text
codex exec --ephemeral
```

因此明确记录：

```text
codex_image_session_reuse = false
```

这是为了避免跨帧上下文污染，也避免在 CLI 尚无可靠 daemon/session API 时伪造“长驻 Codex”。

## Quota Observability

新增：

```text
meta/quota-observability.json
```

自动采集：

- scoped worker JSONL
- image worker JSONL
- 可观察到的 input/output/total token counter
- Step 耗时

不会自动猜：

- Plus 5h 剩余百分比
- Weekly 剩余百分比

如果用户从 `/status` 或产品 UI 看到了真实值，可记录：

```bat
python -X utf8 episodes/_system/story_os.py quota snapshot <episode> --five-hour-remaining 75 --weekly-remaining 88
```

连续生产几篇后，就能计算真实每篇 quota delta。

## 预期效果

这次升级的主要收益首先是：

1. 中断损失显著下降；
2. Story Lock 后剧情不因额度中断而漂移；
3. 观测从“整个 Codex worker 用了多久”细化到四个实际生产步骤；
4. 去掉每帧额外 Python backend 子进程；
5. 为未来真正 Codex transport/session warm pool 留出稳定接口。

不承诺在没有真实生产 telemetry 前直接把 3 小时压到固定 1 小时。

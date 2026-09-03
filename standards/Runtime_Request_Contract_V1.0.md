# Story OS V2.1 Runtime Request Contract V1.0

## 目标

把用户的一句话先编译成稳定、可审计、可恢复的 `runtime-request`，再交给 Story OS 执行。

核心边界：

> Runtime Request 负责“用户要什么、怎么跑”；Concept / Story / Visual 负责“具体怎么创作”。

## 默认行为

- 用户不指定剧情：`story_input.mode=auto_create`，Story OS 必须自己发散 8–12 个候选、通过 Concept Ambition 后写完整故事，不得反问用户补剧情。
- 用户说“剧情大概是…”：`story_input.mode=user_seed`，粗剧情是创作种子，不是 Story Lock；必须强化、补逻辑、重构节奏和高潮，不能机械拆成 20 张。
- 用户说“必须保留/结尾必须…”：`core_constraints`，核心约束必须保留，其余允许优化。
- 只有用户明确说“剧情已经定了/不要改剧情”才进入 `locked_story`。
- 用户不指定 image：默认 `image_model=gpt-image-2`、`image_quality=high`。
- 用户显式指定 image：`strict_model=true`，不得静默替换。
- 新编译请求把 `image_model` / `image_quality` 直接锁在 Runtime Request 顶层；`image` 对象继续保存 provider/source/strict 兼容元数据，两处 model/quality 必须一致。

## 标准请求

```json
{
  "schema_version": 1,
  "mode": "full_auto",
  "repository": {"branch": "story"},
  "topic": {"title": "仲夏夜惊魂"},
  "story_input": {
    "mode": "auto_create",
    "raw": null,
    "constraints": [],
    "rewrite_policy": "auto_create",
    "preserve_core_intent": true,
    "allow_structure_rewrite": true
  },
  "creative_hints": [],
  "image_model": "gpt-image-2",
  "image_quality": "high",
  "image": {
    "provider": "openai",
    "model": "gpt-image-2",
    "source": "system_default",
    "strict_model": false,
    "quality": "high"
  },
  "runtime": {
    "execution_mode": "dag",
    "continuous_execution": true,
    "resume": true,
    "max_image_workers": 3,
    "fail_soft": true,
    "incremental_reuse": true
  },
  "delivery": {
    "mode": "auto",
    "zip_required_for_completion": false
  }
}
```

## 自然语言编译优先级

```text
用户显式要求
>
用户硬约束
>
用户软提示
>
系统默认
```

Runtime Compiler 不得擅自生成：

- climax_frame
- impact_level
- weather contract
- visual lock frame selection
- caption position

这些仍由后续正式 Step 推导。

## Image Model Policy

日常默认：

```text
gpt-image-2
```

需要固定可复现版本时：

```text
gpt-image-2-2026-04-21
```

Codex subscription 路径必须把请求模型一路传递到 Image Worker，并在 Ledger / Worker result 中记录 requested model。若用户显式指定模型，不得由 Story OS 自己改成另一个模型。

正式 Quality 固定为 `high`，必须沿 `Runtime Request → Image Scheduler → Image Worker → Production Ledger` 传递。旧 Runtime Request 缺字段时仅按兼容默认 `high` 读取，不回写不可变请求。

## Visual Lock

V2.1 用户可见和当前机器合同统一为 **4 张 Visual Lock**：

1. ordinary_baseline
2. worst_capture_condition
3. first_major_anomaly
4. high_impact_admission

“3 张校准 + 4 张准入”仅允许出现在明确标记的 legacy compatibility 说明中，不得作为当前 V2.1 Golden Path。

## 一句话入口

无剧情：

```text
读取 story 分支。
全自动做一篇「仲夏夜惊魂」。
```

有粗剧情：

```text
读取 story 分支。
全自动做一篇「仲夏夜惊魂」。

剧情大概是：
……
```

显式模型：

```text
读取 story 分支。
全自动做一篇「仲夏夜惊魂」，image=gpt-image-2。
```

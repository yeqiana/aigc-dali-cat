# WORK Runtime

当前 Story OS 版本以根目录 `story_os_manifest.json` 为准。

## 默认定位

Story OS V2.6.1 起，**WORK 是默认 Runtime**。在 ChatGPT + DevSpace / Work 场景中，当前产品运行时直接负责创作、评审、工具调用和工作区写入；本机是否安装 `codex.exe` 不再影响默认路由。

核心规则：

- 默认生产模式为 `production.mode=COLLABORATIVE`，整体运行时为 WORK。宿主暂时不可用时保持 WORK 并等待/阻塞，不自动改走本地 Codex。
- 执行器配置统一在 `execution`：工作区为 `execution.workspace.provider=webcodex`，图片为 `execution.image.executor=CODEX`，视觉复核为 `execution.vision_review.executor=CODEX`。
- 默认图片执行 Runtime 为 CODEX：**只有图片生成 / 图片返修**显式使用本地 Codex；图片控制模型读取 `models.profiles.image_controller`（当前 `gpt-6-luna` + `high`），图片模型读取 `models.profiles.image_payload`（当前 `gpt-image-2.5-flare` + `quality=high`）。
- Story、PREIMAGE、Critic、Review、Gate、Release 仍由 WORK 负责；图片 Runtime 不得升级成 Codex full-auto。
- 若要显式切换整条生产链，在 `production.mode` 设为 `CODEX_MANAGED`，或单次设置 `STORY_OS_PRODUCTION_MODE=CODEX_MANAGED`。`STORY_OS_RUNTIME` 只保留为兼容/诊断信息，不改变 Production 的 effective mode/runtime。
- 图片执行可用 `STORY_OS_IMAGE_EXECUTOR=CODEX|PRODUCT_RUNTIME|AUTO` 临时覆盖；旧变量 `STORY_OS_IMAGE_RUNTIME` 暂保留为兼容别名。

## 执行方式

用户给出目标任务并授权全自动后：

```text
ChatGPT Product Runtime
→ DevSpace / workspace
→ Story OS deterministic scripts
→ Product-host Story / PREIMAGE / Review
→ CODEX image execution only
→ canonical machine/evidence gates
→ meta/episode-state.json
```

`python episodes/_system/story_os.py run <episode> --full-auto` 在 WORK 下会进入 canonical Runtime DAG；DAG 仍只是执行器，阶段权威继续只有 `<episode>/meta/episode-state.json`。

非图片 Host Action 会写入 `<episode>/meta/runtime/product-host-request.json`（当前指针）以及 `<episode>/meta/runtime/host-requests/<request_id>.json`（不可覆盖历史），同时由 `<episode>/meta/runtime/next-action.json` 给出当前唯一派生下一步。已经完成的旧 Host Request 会按当前阶段/证据自动对账，避免恢复时重复卡在同一步。

`PREIMAGE_COMPILE` 是独立 Runtime DAG 节点，但不是新的 Episode Stage。图片步骤只在 `execution.image.executor=CODEX` 时进入 Codex image worker；Story、PREIMAGE、Critic、Review、Gate、Release 不会因此进入 `scoped_codex_worker` 或 Codex full-auto。

Visual Lock baseline 与每个 Production Logical Batch 生成后都会回到 WORK 做实际像素审核；明确失败帧才进入返修，审核完成后继续下一 Runtime Action。

## 独立 Critic

Concept / Story Critic 不再硬绑定 `CODEX_ISOLATED`。

WORK 使用：

`WORK_ISOLATED`

标准流程：

```text
run-critic
→ 写 meta/runtime/reviews/<kind>-attempt-<n>-request.json（attempt 历史不可覆盖）
→ 产品运行时执行新的对抗式 review pass
→ 只写 candidate JSON
→ finalize-review
→ 校验源文件 SHA 未漂移
→ 写正式 review evidence
```

允许的独立来源：

- `WORK_ISOLATED`
- `WEB_ISOLATED`
- `CODEX_ISOLATED`

不得把普通同轮自评伪装成 isolated review。

## 图片

当前默认图片路由：

```text
Runtime=WORK
+ image_execution_runtime=CODEX
→ Codex Subscription image worker (`models.profiles.image_controller`)
→ image_generation (`models.profiles.image_payload`)
→ RAW / candidate 落本地
→ Story OS Normalize / Ledger
→ WORK / Story OS Review 与 Gate
```

这不是 fallback，而是显式的图片执行层配置。Codex 只拿锁定后的 Prompt / Frame Contract / References 做生图或图片返修，**不得重写 Story、Storyboard、Character Contract、PREIMAGE 或 Stage**。

Visual Lock 继续执行真实 1+3 barrier：baseline actual-pixel PASS 前，后三张不得进入正式生成。若临时设置 `STORY_OS_IMAGE_EXECUTOR=PRODUCT_RUNTIME`，才恢复产品图片 Host Request / `HOST_WAIT` 路径。旧 `STORY_OS_IMAGE_RUNTIME` 仍可兼容。

## Checkpoint / Approval

checkpoint 优先写仓库 `<episode>/meta/runtime-checkpoint.json`。

自动审查使用 `delegated_auto_review`，不得伪称用户亲眼审核。最终状态仍只以：

`<episode>/meta/episode-state.json`

为权威。

# WORK Runtime

当前 Story OS 版本以根目录 `story_os_manifest.json` 为准。

## 默认定位

Story OS V2.6.1 起，**WORK 是默认 Runtime**。在 ChatGPT + DevSpace / Work 场景中，当前产品运行时直接负责创作、评审、工具调用和工作区写入；本机是否安装 `codex.exe` 不再影响默认路由。

核心规则：

- 默认 `runtime.preferred_runtime=WORK`。
- 默认 `runtime.image_execution_runtime=CODEX`：**只有图片生成 / 图片返修**显式使用本地 Codex；图片控制模型锁定 `gpt-5.6-sol` + `reasoning=high`，实际图片模型仍为 `gpt-image-2` + `quality=high`。
- Story、PREIMAGE、Critic、Review、Gate、Release 仍由 WORK 负责；图片 Runtime 不得升级成 Codex full-auto。
- 非图片步骤 WORK **不得静默启动本地 Codex**；若需要整套 CODEX Runtime，仍必须显式设置 `STORY_OS_RUNTIME=CODEX`。
- 图片执行可用 `STORY_OS_IMAGE_RUNTIME=CODEX|PRODUCT_RUNTIME|AUTO` 临时覆盖。

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

`python episodes/_system/story_os.py run <episode> --full-auto` 在 WORK 下只负责初始化、校验并生成：

`<episode>/meta/runtime/product-host-request.json`（当前指针）以及 `<episode>/meta/runtime/host-requests/<request_id>.json`（不可覆盖历史）

它不会再进入 `runtime_dag → scoped_codex_worker → codex exec`。

宿主 ChatGPT 读取该 request 后直接执行对应 `next_step`，完成后继续跑确定性 Gate。

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
→ Codex Subscription image worker (`gpt-5.6-sol`, reasoning=high)
→ image_generation (`gpt-image-2`, quality=high)
→ RAW / candidate 落本地
→ Story OS Normalize / Ledger
→ WORK / Story OS Review 与 Gate
```

这不是 fallback，而是显式的图片执行层配置。Codex 只拿锁定后的 Prompt / Frame Contract / References 做生图或图片返修，**不得重写 Story、Storyboard、Character Contract、PREIMAGE 或 Stage**。

Visual Lock 继续执行真实 1+3 barrier：baseline actual-pixel PASS 前，后三张不得进入正式生成。若临时设置 `STORY_OS_IMAGE_RUNTIME=PRODUCT_RUNTIME`，才恢复产品图片 Host Request / `HOST_WAIT` 路径。

## Checkpoint / Approval

checkpoint 优先写仓库 `<episode>/meta/runtime-checkpoint.json`。

自动审查使用 `delegated_auto_review`，不得伪称用户亲眼审核。最终状态仍只以：

`<episode>/meta/episode-state.json`

为权威。

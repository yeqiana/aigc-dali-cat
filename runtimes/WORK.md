# WORK Runtime

当前 Story OS 版本以根目录 `story_os_manifest.json` 为准。

## 默认定位

Story OS V2.6.1 起，**WORK 是默认 Runtime**。在 ChatGPT + DevSpace / Work 场景中，当前产品运行时直接负责创作、评审、工具调用和工作区写入；本机是否安装 `codex.exe` 不再影响默认路由。

核心规则：

- 默认 `runtime.preferred_runtime=WORK`。
- WORK **不得静默启动本地 Codex**。
- 本地 Codex 只在用户/调用方显式设置 `STORY_OS_RUNTIME=CODEX` 或显式传入 Codex 执行入口时启用。
- WORK 缺某项产品能力时必须返回 `HOST_ACTION_REQUIRED`；Checkpoint 记为 `HOST_WAIT`（正常宿主握手，不计作故障 BLOCKED），不得以“兜底”为名消耗本地 Codex 配额。

## 执行方式

用户给出目标任务并授权全自动后：

```text
ChatGPT Product Runtime
→ DevSpace / workspace
→ Story OS deterministic scripts
→ Product-host review / image actions
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

Provider 顺序：

```text
OPENAI_API_KEY 存在
→ OpenAI Image API

否则 Runtime=WORK/WEB
→ product_runtime_image

只有 Runtime=CODEX
→ Codex Subscription
```

WORK 图片任务由 `meta/runtime/product-host-request.json` 暴露待生成帧、Prompt、Reference、模型与 Frame Contract。

如果当前产品运行时可以把真实生成图片保存/导入工作区，就继续 Normalize / Ledger / Review；如果产品图片工具无法把文件送入仓库，必须暂停为 `HOST_ACTION_REQUIRED`，**禁止自动回退本地 Codex**。

## Checkpoint / Approval

checkpoint 优先写仓库 `<episode>/meta/runtime-checkpoint.json`。

自动审查使用 `delegated_auto_review`，不得伪称用户亲眼审核。最终状态仍只以：

`<episode>/meta/episode-state.json`

为权威。

# Story OS V2.1 Runtime Performance Pack P0.7–P1.2 V1.0

本规范与 Runtime Refactor P0.5/P0.6 **一次安装**。

目标：不删除任何 Story / Visual / Production / Release 正式验收，只消灭等待、重复上下文与重复编译。

## P0.7 Continuous Image Scheduler

- 最多 3 个 image worker 不变。
- 不再采用“整波全部结束后才能开下一波”。
- 任一 worker 完成后，主线程单写 Ledger，随后立即补充下一个 READY frame。
- adaptive 3→2→1、fail-soft、技术失败不消耗内容返修继续保留。

## P0.8 Execution Capsule

每个 Scoped Codex Step 先读取：

```text
meta/runtime/execution-capsules/<step>.json
```

Capsule 由 Python 编译并绑定：
- Runtime Request
- 当前 Episode state
- Workflow Contract 关键 invariant
- 权威文件 SHA
- 当前 Step evidence

它只是 derived cache；和原始规范冲突时原始权威文件优先。

## P0.9 Safe DAG Parallel Lane

Story Lock 完成后，允许 `provisional_release.py` 在 runtime-only 路径后台生成文字草稿，与后续 Visual/Production 主链重叠。

不会并行写：
- Story
- release-manifest
- Final Candidate Snapshot
- Episode state

## P1.0 Rolling Pre-Final Review

只对高风险生成帧提前 actual-pixel 预审：

```text
PASS_PREVIEW
REPAIR_NOW
UNCERTAIN
```

`PASS_PREVIEW` 永远不是 final PASS；正式 Final Frame Review 继续保留。

## P1.1 Prompt Package Compiler

每帧写：

```text
meta/runtime/prompt-packages/NN.json
```

绑定：
- scene prompt SHA
- Resolved Frame Contract SHA
- image model
- package SHA

Frame Contract 或 scene 变化时包自动失效。

## P1.2 Provisional Release Pipeline

Story Lock 后可提前草拟：
- 标题
- 简介
- 封面文案
- 字幕语义草稿
- 话题候选

仅写：

```text
meta/runtime/provisional-release.json
```

Production PASS 后必须结合最终图片正式 Finalize；草稿不能推进 Stage，也不能修改 release-manifest / Snapshot。

## 不变的质量底线

- `meta/episode-state.json` 仍是唯一 Stage 权威。
- 4 张 Visual Lock 不变。
- Final Frame Review 不删。
- Final Candidate Snapshot / Release Gate 不删。
- Production Ledger 仍然单写。
- image max workers 仍为 3。
- Codex image conversation 仍隔离，不伪造持久 session。

# EP003 Production Hardening Report

日期：2026-09-12

## 回归对象

`episodes/_archive/20260911_EP003_abandoned_雾中的另一座生活区`

EP003 已归档且不属于可恢复的正式生产 Episode。本次只读验证；没有写入 `meta/story-dna-trace.json`、`meta/visual-reality-score.json` 或任何 approval/gate PASS。

## 新 Gate 结果

- Story DNA Trace：`Historical Evidence Missing: meta/story-dna-trace.json`
- Visual Reality Score：`Historical Evidence Missing: meta/visual-reality-score.json`
- Reference Execution Receipt：`reference execution receipt missing`
- `machine_gate.validate(..., "PUBLISH_READY")`：还报告历史 `missing_asset` 与 `frame_semantic_review`；不存在可被解释为成功的兼容分支。
- Repair 路径：Visual Reality 缺失/低分被分类为 `repair_visual_reality`，但本次没有生成或修复任何历史媒体。
- 结论：历史 Episode 缺失新证据时不能进入 `PUBLISH_READY`；结果是 FAIL/缺证据，而不是兼容性 PASS。

## W-17 / W-20 / W-21 回归

- W-17 身份锚执行链：Reference Execution Evidence 测试覆盖 provider receipt、参考锚点及 SHA 漂移；漂移或缺锚必须 FAIL。
- W-20 AUTH 分类：沿用既有运行时真实错误分类链；本轮没有把认证/配额/落盘错误重写为配置通过。
- W-21 Required Fields：缺 `reference_execution`、`provider_receipt_id` 或 `verified` 均由 Evidence Gate 报 FAIL。

## 实测命令

- `pytest tests/system/test_v3_production_hardening.py -v`：5 passed。
- `pytest tests/system/test_reference_execution_evidence.py -v`：18 passed。
- `pytest tests/system/test_story_semantic_trace.py -v`：26 passed。

## 边界

Reference Execution Receipt 和 Evidence Gate 的既有真实执行证据能力已存在，本次没有重复实现。`episode-state.json` 未被修改，仍是唯一阶段事实源。

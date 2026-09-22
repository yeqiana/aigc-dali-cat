# 《雾中的另一座生活区》生产验收记录

## 验收结论

生产门禁通过。本集 20 张正文帧全部为已批准锁定资产，画幅 4:5（1080 × 1350），逐帧 SHA 绑定实际像素语义复审 PASS，生产台账 20/20 PASSED，近重复审计 PASS。

## 生产事实

- Visual Lock 采用 V2.1 四层准入：Frame01（ordinary baseline）/ Frame06（worst capture condition）/ Frame03（first major anomaly）/ Frame19（high-impact admission），四张为四个不同图号。
- 角色身份沿用系列身份锚（EP001 已批准情侣自拍 + P02 正侧脸）；本集不重新选脸。
- Frame15 由用户直接指出「女生手臂明显不对」（手臂跨帧过长偏粗、手腕与前臂衔接不自然、掌指结构失真、袖口与手臂融合），按用户点名返修通道授权重做：新 prompt 只增加手部解剖约束，身份、服装、器材、天气与 impact 均未改动；其余已通过且 SHA 未漂移的帧一律复用。
- 唯一核心异常仍是「同一空间出现另一座仍在正常生活的山谷聚落」，未引入第二机制，也未解释来源。

## 机器证据

- `meta/production-ledger.json`：20/20 PASSED，canvas 1080 × 1350，逐帧 approved asset SHA 校验通过。
- `meta/frame-reviews/01-20.json`：逐帧结构化真实性审查齐全（viewpoint_physics / capture_profile_match / not_cinematic / album_test 均 PASS）。
- `meta/frame-semantic-review.json`：attempt 2，FULL_FRAME_SET，绑定当前批准像素 SHA；`meta/incremental-frame-audit.json` PASS。
- `machine_gate.py --target PRODUCTION_PASSED` 与 `evidence_gate.py --target PRODUCTION_PASSED`：PASS。
- `meta/text-audit.json`：hard=0、warnings=0；`meta/subtitle-voice-review.json`：连续三图 / 朗读 / 删字幕 / 知识边界 / 线索后果五项 PASS。
- `meta/temporal-continuity.json`：LOCKED，绑定 world-state SHA，validate PASS。

## 已知边界

- 发布渲染（`subtitle_layout.py render-all` 与字幕位置审计）、封面、发布文案与传播卡属于 RELEASE 阶段，本记录不作为发布资产证据。
- Frame15 修复后的手臂自然度仍需用户肉眼终判；本记录不替代人工终审。

## 说明

本作是虚构演绎，非真实事件记录；人物、地点、情节均为虚构，画面由 AI 生成。

# 《误入桃花源》生产验收记录

## 验收结论

用户于 2026-09-23T16:13:35+08:00 以直接用户决策记录接受当前 20 张资产为终稿、接受发布物携带已知缺陷，并继续完成整篇生产（meta/runtime/final-acceptance-events.jsonl，basis=direct_user_review，accepted_scopes=fast_frame_scout / frame_semantic / production_gate / story_semantic_trace）。本记录如实登记该受控例外，不把已知缺陷改写为通过，也不代表用户逐张亲眼复核过画面。

## 最终资产

- 20 张 4:5（1080 × 1350）正式帧，由 production ledger 权威中的 approved 像素经 canonical 字幕渲染输出到 production/publish/01..20.png；封面为 production/cover/cover.png（帧 01 approved 像素 + 标题文字合成，与正文首图同场景近邻帧，避免封面→正文首图 bait-and-switch，做法与 09_旧物怪谈/05 先例一致）。
- 20/20 帧 ledger status=PASSED/LOCKED，SHA 与磁盘一致；production_ledger.py audit --require-passed PASS。
- meta/subtitle-layout-audit.json：canonical renderer 输出，20/20 帧，左对齐 x=72、落在左中安全区，PASS。
- meta/text-audit.json：hard=0，warnings=0。
- meta/visual-lock-baseline-review.json：ordinary_baseline decision=PASS、status=LOCKED（帧 01）。
- 帧 01/03/05/15 与 09 为用户直接合同例外下的旧合同像素（meta/runtime/frame-contract-exceptions.json），未按新版合同重生成。

## 已知缺陷清单（用户接受）

- meta/.frame-semantic-review.candidate.json（attempt-scoped 候选）summary.passed=false，仅 07/17/18 通过；该 FAIL 证据原样保留，未执行失败候选，未据此清空任何 approved 资产或 LOCK。
- 用户终稿接受携带缺陷的帧：01、02、03、04、05、06、08、09、10、11、12、13、14、15、16、19、20。
- Fast Scout 的 REPAIR_NOW / stale 记录原样保留（meta/frame-scout-summary.json）。
- quality.production_gate 保持 pending：本记录不冒充生产门禁通过；机器门禁仅在存在本集 final-acceptance 记录时将其降级为 WARN，证据文件不改写。

## 本次收口动作（可审计）

- Redis 权威 production queue 丢失历史 visual-lock baseline 行（队列于 2026-09-23T00:14 在 Redis 重建时未携带该行），BASELINE_GATE 因此报 ordinary_baseline frame 01 is not generated。依据 meta/image-workers/01-7a7a09d14bde-a4.lifecycle.json 记载的既有生成事实，把该行以原 item_id 7a7a09d14bde 补回队列（status=generated，output_path 指向已审核通过的 baseline 资产），未生成任何新图。
- 本地 sink meta/runtime/trace-events.jsonl 与 meta/episode-performance-ledger.json 缺失，按其权威来源（MySQL runtime trace facts / episode performance 文档）在本地补齐投影，runtime_evidence_contract.verify 返回无错误。
- visual_lock delegated 审批在 meta/visual-profile.json 生命周期 freeze（2026-09-23T03:18）后出现 SHA 漂移，按同一 full-auto 授权重签；四张准入帧像素 SHA 未变。

## 例外依据

- meta/runtime/final-acceptance-events.jsonl：event=FINAL_ACCEPTANCE_RECORDED，basis=direct_user_review。
- meta/runtime/frame-contract-exceptions.json：帧 01/03/05/15/09 的 direct_user_contract_exception。
- meta/publish-compliance.json：AI 生成声明与虚构语境声明在发布时必须由人工在平台侧确认。
- story-gates.reviews 口径：continuity 为字面 passed（该字段没有 waive 通道，与同仓 11_仲夏夜惊魂/01_停电夜蜕壳 先例一致）；production 与 subtitle 记 waived、subtitles.sound_card_completed 保持 false，由本集 final-acceptance 的 production_gate scope 降级为 WARN，不冒充通过；recommendation_fit 与 publish 按用户终稿接受决定记 passed。

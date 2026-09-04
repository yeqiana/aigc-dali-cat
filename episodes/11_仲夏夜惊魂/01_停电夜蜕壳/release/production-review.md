# 《停电夜蜕壳》生产验收记录

## 验收结论

用户直接声明接受当前资产为终稿、接受发布物携带已知缺陷，并选定受控例外放行方案（`meta/final-acceptance.json`）。本记录作为生产收尾文档，不把已知缺陷改写为通过。

## 最终资产

- 20 张 4:5（1080 × 1350）正式帧已从最终 approved 像素（含 03/08/18 单次内容返修后的 promote 资产）全部重渲染字幕并写入 `production/publish/`。
- 帧 07/09/14/16 为用户终稿决定的 LOCKED 资产；03/08/18 为 2026-09-04 09:50 返修候选，ledger status=PASSED 且 SHA 与磁盘一致；其余帧 LOCKED(PASSED)。成功帧未因同批其他帧技术失败而重生。
- `meta/subtitle-layout-audit.json`：重新渲染后 PASS（20/20）。
- `meta/text-audit.json`：hard=0，warnings=4（字幕长度均匀性提示，非硬错误）。
- `meta/frame-semantic-review.json`：summary.passed=false 的 attempt-2 记录原样保留，作为已知缺陷证据。
- `meta/frame-scout-summary.json`：07/08/10/13/14/16/20 的 stale/REPAIR_NOW 记录原样保留。

## 已知缺陷清单（用户接受）

- 帧语义评审 FAIL 10 帧（03/06/07/08/09/10/14/16/17/20），含 ANOMALY_UNREADABLE、KEY_PROP_DRIFT、CAPTION_DEPENDENCY、ANOMALY_SCALE_UNDERDELIVERED、CAMERA_OWNER_UNRESOLVED 等，细节见 `meta/frame-semantic-review.json`。
- 帧 07/08/10/13/14/16/20 Fast Scout 未消除 REPAIR_NOW/stale。
- 03/08/18 返修后未跑 full-set critic 终裁即由用户叫停，按用户终稿决定放行。

## 例外依据

- `meta/final-acceptance.json`：decision=accept_current_as_final，basis=direct_user_review。
- 机器门禁（machine_gate / validate_episode / final_candidate_snapshot）仅在存在本集 final-acceptance.json 时对上述内容门禁降级为 WARN；证据文件不改写，其他剧集门禁不受影响。

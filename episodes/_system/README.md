# Episodes 状态机 + Story OS 门禁 V2.0.2

本目录只建立一套机器阶段状态；V2.0.2 延续 V1.8 引入的证据 SHA 门禁，并增加稳定 evidence gate 与可执行 Codex runtime，不新增第二状态机。

## 核心事实源

```text
<episode>/meta/
├── episode-state.json       # 唯一阶段事实源
├── release-manifest.json    # 最终发布版本事实
├── story-gates.json         # 门禁配置与证据索引，不保存 stage
├── production-ledger.json   # 逐帧生产事务
└── frame-reviews/NN.json    # 严格模式逐帧真实性审查
```

## 状态机

```text
IDEA_LOCKED
→ STORYBOARD_LOCKED
→ VISUAL_CALIBRATED
→ PRODUCTION_PASSED
→ PUBLISH_READY
→ PUBLISHED
→ DATA_REVIEWED
```

正向只能相邻推进；正向推进依次运行 `validate_episode.py`、`machine_gate.py`、`evidence_gate.py`。任一失败，状态不变化。

## 新项目

```bash
python episodes/_system/episode_state.py init \
  episodes/10_新系列/01_新故事 \
  --id 10-01 --series 10_新系列 --title "新故事" --frame-count 20

python episodes/_system/evidence_tool.py init-reviews episodes/10_新系列/01_新故事
```

新项目默认 `machine_contract.strict=true`。

## 旧项目

旧项目不自动伪造任何通过证据：

```bash
python episodes/_system/episode_state.py migrate-gates <episode_dir>
# 默认 strict=false

# 真正重新进入制作后，再显式开启：
python episodes/_system/episode_state.py enable-machine-gates <episode_dir>
```

## VISUAL_CALIBRATED 机器证据

严格模式必须有：

- 完整真实性卡：年代、地点、拍摄者、拍摄原因、主设备、稳定/受限/失控三种状态；
- 辅助采集设备最多两种，且有剧情来源；
- 第一视角设备/拍摄者完整入镜时有物理解释；
- 三张校准：`baseline / worst_condition / first_major_anomaly`；
- 三张图号不同，且必须属于四张视觉准入帧；
- 三张校准图与校准联系表保存 SHA-256；
- 若 reference policy 标记为 required，则每个 required anchor 都有 passed + hash 锁定资产。

记录校准：

```bash
python episodes/_system/evidence_tool.py record-calibration <episode_dir> \
  --role baseline --frame 01 --asset <01.png> --decision passed

python episodes/_system/calibration_sheet.py <episode_dir>
python episodes/_system/machine_gate.py <episode_dir> --target VISUAL_CALIBRATED
```

## PRODUCTION_PASSED 机器证据

严格模式还要求：

- production ledger 帧数与 manifest 一致；
- 每帧状态只能是 PASSED / LOCKED；
- 每帧最多一次内容返修；
- 每帧有 approved asset + SHA；
- LOCKED 帧 lock hash 等于 approved hash；
- 每帧都有 `meta/frame-reviews/NN.json`；
- `viewpoint_physics / capture_profile_match / not_cinematic / album_test` 必须 pass；
- identity / prop / location / continuity 等字段不能 fail；
- 有效摄影红旗 >=3 直接失败；
- 豁免必须是 detected 子集且有预登记原因；
- review decision 为 repair / must_regenerate 时不得进入生产通过态。

```bash
python episodes/_system/evidence_tool.py init-reviews <episode_dir>
python episodes/_system/machine_gate.py <episode_dir> --target PRODUCTION_PASSED
```

## CI

```bash
python -m compileall -q episodes/_system skills/dali-cat-story
python episodes/_system/test_validator.py -v
python episodes/_system/test_machine_gate.py -v
python episodes/_system/validate_episode.py --all --metadata-only
python episodes/_system/machine_gate.py --all --metadata-only
```

`--metadata-only` 只用于 CI，避免要求仓库中未跟踪的本地图片二进制。正式本地推进必须执行完整验证。

## 边界

机器只验证硬证据，不替代：手机相册真实感、继续滑动欲望、角色“像不像同一个人”、高潮强度和结尾回看价值。这些仍由人工/多模态终审决定。

<!-- STORY_OS_V1_8_SYSTEM_README_BEGIN -->
## Story OS V1.8 增量门禁

- 未指定画风：默认 `M00｜MP4 × 网吧 × 流水席旧数码质感校准版`；实际年代/采集设备物理表现优先。
- `STORYBOARD_LOCKED`：Story Lock 必须有用户批准 + story/storyboard SHA。
- `VISUAL_CALIBRATED`：Visual Lock 必须有用户批准 + visual spec / 校准 / reference / resolved profile SHA。
- `PUBLISH_READY`：`meta/text-audit.json` 必须 PASS 且 `source_sha256` 等于当前 captions。
- `PUBLISH_READY`：`meta/release-package.json` 必须用户批准，且封面/正文/字幕/发布文案/传播卡 SHA 全部一致。

V1.7 的 transport guard 与 text revision transaction 继续沿用，不重复实现。
<!-- STORY_OS_V1_8_SYSTEM_README_END -->

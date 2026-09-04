# V2.2.1 PREPRODUCTION ACCEPTANCE REPORT

Episode：`episodes/11_仲夏夜惊魂/01_惊魂`（《仲夏夜惊魂》重制版）

执行模式：`PREPRODUCTION_ONLY`

结论：正式生产前资产已补齐，机器验证全 PASS，可以进入 Visual Lock（等待用户显式授权执行）。

## 1. 当前 Episode 状态

- `meta/episode-state.json`：`current_state = IDEA_LOCKED`，`tool_version = 2.2.1`
- `meta/story-gates.json`：Story Lock `PASS` / Character Contract `PASS` / World Identity `PASS` / Visual Narrative `LOCKED` / Production `NOT_READY`
- 未生成任何图片，未进入 Production，未提交 Git。

## 2. 新增文件列表

本次补齐/升级的资产（相对 Episode 目录）：

| 文件 | 用途 |
| --- | --- |
| `meta/character-contract.json` | 官方机器角色契约（LOCKED，P01+P02 pair） |
| `meta/character-visual-contract.json` | 角色视觉规格（LOCKED，identity_spec_locked） |
| `meta/shot-progression-review.json` | 20 帧 Visual Narrative 机器契约（schema 2 LOCKED） |
| `meta/visual-narrative-core.json` | 人读版 20 帧叙事契约（用户要求字段） |
| `meta/Environment_Contract.json` | 人读版环境契约（用户要求） |
| `meta/episode-state.json` | 唯一机器阶段事实源（IDEA_LOCKED） |
| `meta/runtime/contracts/character-appearance-anchor.json` | 官方派生外观锚点（CLI build 生成） |
| `contracts/Character_Contract.json` | 升级版角色契约（人读镜像） |
| `contracts/Character_Appearance_Anchor.json` | 外观锚点人读规范（P01/P02 + same_person） |
| `docs/V221_PREPRODUCTION_ACCEPTANCE_REPORT.md` | 本报告 |

既有资产 `meta/story-gates.json`、`meta/release-manifest.json` 由本次任务建立（tool_version 2.2.1）。

## 3. Story Lock 验证结果

- 源文件核读：`docs/Story_Lock_V2.2.1_仲夏夜惊魂重制版.md`，核心方向未改动。
- 主角符合 `CN_MAINLAND_YOUNG_ADULT_DEFAULT_V1`：P01 25 岁普通中国年轻男性，职业仅解释返乡不解决异常。
- P02 妹妹规则核读通过：老家妹妹、20 岁、年轻漂亮但真实普通、不是解释者、不是剧情工具人、与哥哥为自然亲兄妹关系。
- 第一人称规则核读通过：观众沉浸视角，不是摄影取证任务。
- 四项禁止规则已写入本 Episode Gate（`meta/story-gates.json` 的 `story.narrative_policy.forbidden_endings`）：
  - 禁止最后照片解释异常（last_photo_reveal）
  - 禁止手机回放揭示真相（phone_replay_reveal）
  - 禁止相册反转（album_reversal）
  - 禁止静默反转结尾（silent_twist）
- Story Lock 无独立机器校验命令，采用人工核读 + Gate 状态记录；机器侧由后续环境/叙事契约间接绑定。

## 4. Character Continuity 验证结果

命令输出（PASS）：

```text
CHARACTER CONTRACT VERIFIED
VERIFIED   # character_visual_contract.py validate
CHARACTER APPEARANCE ANCHOR VERIFIED
```

- 使用命令：`character_contract.py validate --require-locked`、`character_visual_contract.py validate`、`character_appearance_anchor.py build/verify`。
- P01/P02 在同一角色池边界（modern_2020s，年龄 19-30，普通体型/服饰基线），`same_person_across_frames=true`。
- Character Contract / Character Visual Contract 均 LOCKED，world identity 字段（nationality/resident/effective_sha256）已注入并与 World Identity effective 一致。
- NO-ANOMALY TEST PASS，`rechecked_against_final_story=true`，ordinary_person_score=100，无 forbidden role hit。

## 5. World Identity 验证结果

命令输出（PASS）：

```text
WORLD IDENTITY CONTRACT VERIFIED
```

- 使用命令：`story_world_identity.py verify`。
- Effective profile：`CN_MAINLAND_YOUNG_ADULT_DEFAULT_V1`（中国大陆、Mainland China、Chinese、mainland Chinese local residents），`effective_sha256=98e4e6df...`。
- 本 Episode 未建机器 override；工具读取的是 `meta/world-identity.json`（连字符）。当前目录内既有 `meta/world_identity.json`（下划线）为信息性资产，工具不读它也不报错，两者已在本报告与资产备注中区分，避免误解。
- 环境禁止规则（欧美住宅 / 日韩街景 / 非中国生活符号）已写入 `meta/story-gates.json` 与 `meta/Environment_Contract.json`。

## 6. Visual Narrative 验证结果

命令输出（PASS）：

```text
VISUAL NARRATIVE CORE VERIFIED mode=production frames=20 authority=PREPRODUCTION_DERIVED_CONTRACT
ENVIRONMENT CONTRACT VERIFIED
V2.2.1 PREIMAGE READINESS PASS | world_identity=PASS character_anchor=PASS visual_narrative=PASS
```

- 使用命令：`story_visual_narrative.py verify`、`environment_contract.py verify`、`story_v221_readiness.py --stage preimage`。
- `meta/shot-progression-review.json`：schema 2 + LOCKED，20 帧与 manifest `body_frame_count=20` 一致，逐帧字段/异常阶段/人类行动/情绪/互动密度全部通过机器门禁。
- 叙事设计不含静默反转与最后照片揭秘：异常始终不解释；结尾为事件高潮 + 人物行动 + 情绪释放（第三次循环参照 → 推车 → 拖拉机强光归位 → 门灯收束）。
- Frame 17（高潮）与 story-gates `climax_frame` 绑定，环境契约与逐帧指令全部验证通过。

## 7. 是否可以进入 Visual Lock

是。V2.2.1 PREIMAGE READINESS 全 PASS，四份前置契约（角色、角色视觉、外观锚点、20 帧叙事）已 LOCKED，环境契约与逐帧指令完整。

进入 Visual Lock 前需满足的边界：

- 本报告不代表 Visual Lock 已执行：四张校准帧（ordinary baseline / worst condition / first anomaly / high-impact admission）尚未生成，需等待用户显式授权进入视觉执行阶段。
- Visual Lock 相关像素资产仍未生成，禁止把本报告当作已通过视觉验收的证据。

【目标】补全《仲夏夜惊魂》重制版 V2.2.1 正式生产前资产并完成机器验收
【改动文件】character/visual/shot-progression/episode-state 等 10 个前期资产（见第 2 节）
【风险】人读镜像文件与机器权威文件并行，以 meta 机器文件为准；world_identity 下划线文件名与工具连字符路径差异已说明
【必须验收】用户授权后执行 4 帧 Visual Lock；验收前禁止生图/Production/Git
【结论】机器验证全 PASS，可以进入 Visual Lock

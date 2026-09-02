# V22_PRODUCTION_PILOT_REPORT

> Story OS V2.2 Production Pilot ·《仲夏夜惊魂｜蝉声停的夏至夜》
> Episode: `11-V22P`（`episodes/11_仲夏夜惊魂/V22_PILOT_TEST`，独立测试，未覆盖旧版本）
> Branch: story · Tool Version: 2.2.0 · Visual Narrative Core V2.2: 正式激活（production / PREPRODUCTION_DERIVED_CONTRACT）
> Scope: Story Lock → Character → Environment → Visual Narrative → Resolved Frame Contract(20) → Visual Lock 测试帧 01-05 测试图
> 不含 Production Full Batch / Release / Publish；机器阶段保持 `IDEA_LOCKED`，不推进正式 stage
> Authority: `V22_PRODUCTION_PILOT_TEST`（测试证据；正式发布/门禁不以此为准）
> 图片来源边界：本报告基于对已生成测试图（`media/v22-pilot/out/01-05.png`）与逐帧合同/提示词的人工交叉核验；生成 attempt 级机器日志不在仓库内，模型/attempt 明细未能在本次复核中独立取证。

## 0. Phase-1 Readiness（第一阶段确认）

| 项 | 结果 | 证据 |
| --- | --- | --- |
| Story OS 版本 | 2.2.0 | `story_os_manifest.json`、`episode-state.json`、`story-gates.json` 均 `tool_version=2.2.0` |
| Photography OS / Capture Grammar | 已启用 | `FIRST_PERSON_CASUAL_SNAPSHOT_V1`（blueprint + 全部 frame contract） |
| Visual Narrative Core V2.2 | 已启用 | `visual_narrative_core_v22.py verify` → `mode=production frames=20 authority=PREPRODUCTION_DERIVED_CONTRACT`，无 errors |
| Environment Contract | 通过 | `environment_contract.verify` → `[]` |
| Resolved Frame Contract | 20/20 完整 | 每帧含 `hash_material.visual_narrative`（core_id=VISUAL_NARRATIVE_CORE_V2.2）与 `visual_narrative_sha256`；`frame-contract-index.json` 齐备 |
| Shot Progression | 20 帧 LOCKED | `meta/shot-progression-review.json` schema-2，六问字段全部填齐 |

`V22_PRODUCTION_PILOT_READY = PASS`

## 1. Story Quality

故事骨架（非逐帧图内可读内容）：普通返乡年轻人（P01，25 岁，办公室工作）+ 弟弟（P02，22 岁）的夏至夜：回老屋吃瓜 → 骑车去镇区买冰西瓜 → 回家后相册出现"不是他拍的、机位却物理成立"的照片，蝉声随之整片停。删除异常后的一天仍完全成立（NO-ANOMALY TEST PASS）；主角不做职业化调查、不追捕异常、天亮保留照片照常生活。

1. 不是传统恐怖片：前 5 帧 0 恐怖符号，全部是普通夏夜生活素材（门灯、西瓜、电动车、河堤、夜市远景）。
2. 异常在 F09 后才入场，且以"私人相册被侵入"这一极生活化、非可见的形态出现。
3. 动机全是普通人的真实拍摄理由：发爸妈、发家庭群、发同事、留证、留一张照片。

**8.5 / 10**

## 2. Camera Authorship（谁拍的？为什么此刻拍？摄影者在哪里？）

| Frame | 合同持机 | 图中可见的持机/画面证据 | 判定 |
| --- | --- | --- | --- |
| 01 | P01 第一人称主摄（院门口） | 画面=门灯下弟弟端瓜盆迎出来，前景门框生活痕迹；机位在门口站定处 | 可解释，POV 成立度一般（主体正面居中，第一人称偏弱） |
| 02 | P02 拿哥哥手机前置自拍 | 画面=前摄广角自拍、手臂前伸、轻微歪斜、哥哥咬瓜笑 | 成立（自拍来源明确） |
| 03 | P01 主摄（屋檐下） | 画面=弟弟蹲在电动车后座旁绑袋子，背心汗湿；车/物件前景 | 成立（无来源第三人称，纯记录动作） |
| 04 | P01 主摄，拍坐后座喝水的弟弟 | 画面=持机者在画面前景出现大半身/肩部，主体落在中景 | 构图偏"自拍"，与合同 POV 描述不完全一致 |
| 05 | P02 副摄（坐后座拍哥哥） | 画面=后座机位，哥哥站在路沿举手机朝河、回头；车把/后视镜入画前景 | 成立（companion_secondary_p02_shot 完全兑现） |

第二持机者规则（P02 仅在剧情有物理理由时持机）在 02/05 兑现；无幽灵摄影机、无导演/上帝/电影机位。01、04 存在"主摄把自己一起拍进去"的执行偏差，属于 POV 构图偏离而非来源不成立。

**7 / 10**（01/04 两帧 POV 执行偏差扣分；来源全部可解释，未触犯禁止项）

## 3. Moment Contract（当时发生什么动作？人物情绪？新增什么信息？）

| Frame | 动作中的瞬间 | 情绪 | 新增信息 | 判定 |
| --- | --- | --- | --- | --- |
| 01 | 弟弟端瓜盆迎出来抬头喊 | 松弛（热一天到家） | 老屋/兄弟/晚饭=瓜 | PASS |
| 02 | 哥哥咬着瓜笑、弟弟举手机 | 轻松好笑 | 弟弟会用哥哥手机（后续核对基础） | PASS |
| 03 | 绑袋子准备出门，动作进行中 | 普通/热 | 出门计划+车辆特征第一次入画 | PASS |
| 04 | 停车回消息、后座喝水的间隙 | 普通夏夜放松 | 路线/时间/远处镇区灯火 | PASS（构图偏差见 2） |
| 05 | 喊话回头、哥哥方向偏了 | 松弛起哄 | 第二持机者 P02+浅蓝手机正式出现 | PASS |

全部 5 帧都是"动作进行中的随手记录"，无摆拍合影感（02 自拍除外，且自拍理由成立）。

**8.5 / 10**

## 4. Narrative Evidence Diversity

机位族不重复：门框正面 / 前摄自拍 / 蹲位侧后 / 站立近景 / 后座副摄；5 帧覆盖 5 类 setup 与 4 个不同场景（老屋门口→堂屋→院车棚→河堤），无相邻构图复制。信息上 01-05 是纯 setup/transition 的正常底片堆叠，各自承担"建立"职责（人物、关系、出门计划、路线、第二持机者），互不冗余。

**8 / 10**

## 5. Private Album Feel（真实摄影感六查）

| 维度 | 01 | 02 | 03 | 04 | 05 |
| --- | --- | --- | --- | --- | --- |
| 手机随手拍（无电影光/海报构图） | 通过 | 通过 | 通过 | 通过 | 通过 |
| 不摆拍（动作进行中） | 通过 | 自拍例外 | 通过 | 通过 | 通过 |
| 环境/生活密度（门框、瓜盆、饭桌、车棚、河堤、夜市灯光） | 通过 | 通过 | 通过 | 通过 | 通过 |
| 天气/季节因素（闷热夜色、汗湿、路灯飞虫感、热浪夜色） | 通过 | 通过 | 通过 | 通过 | 通过 |
| 人物反应（喊话、咬瓜笑、绑袋、喝水、回头） | 通过 | 通过 | 通过 | 通过 | 通过 |
| 空气感/细节缺陷（轻度噪点、手持倾斜、暗部层次、灯色） | 通过 | 通过 | 通过 | 通过 | 通过 |

**9 / 10**（POV 偏自拍的两帧拉低少许，其余接近"手机相册原片"）

## 6. Compared with V2.1

提升点：
1. 环境合同下沉到逐帧：闷热/汗/路灯色/夜景噪点成为物理连续量，不再靠统一"旧质感"滤镜背书。
2. Camera Authorship 变成帧级硬约束：第二持机者全部登记物理理由，05 的后座副摄机位在像素上兑现。
3. 正常底片(F01-08)把"日常"压到足够真实，使后续 F09 相册异常只靠"机位成立但没人/站不了人"产生张力，不需要恐怖视觉。

问题：
1. F01/F04 两帧出现"第一人称主摄把自己拍进画面"的构图漂移，说明纯文字 prompt 约束 POV 仍不够稳，需要强化"相机侧/主体偏置"措辞或对拍后复核。
2. F03 的"断一边后视镜"细节在生成图里不清晰，车辆特征锚点要在正式批次中提高要求（放大校验或后补标识）。
3. 静止照片无法承载"蝉声停/空气扭曲"两个关键环境记号，需靠视频/字幕/文案补，不能指望单图。

## 7. Frame Review（人工逐张像素级审读）

| Frame | 合同核心 | 结果 | 备注 |
| --- | --- | --- | --- |
| Frame 01 | 门灯下弟弟端瓜盆迎出来（P01 主摄） | PASS | 图像可读、生活密度真实；POV 构图偏正面，正式批前建议加"肩侧偏置"约束 |
| Frame 02 | 前摄自拍发家庭群，哥哥咬瓜 | PASS | 自拍成立、广角前摄物理正确 |
| Frame 03 | 绑袋准备出门、车辆特征入画 | PASS | 动作进行中成立；断后视镜细节弱，正式批须提高校验 |
| Frame 04 | 河堤停车，拍后座喝水 | PASS | 主体成立；构图偏自拍，与合同 POV 有偏差，值得返修观察 |
| Frame 05 | P02 后座副摄拍路沿的哥哥 | PASS | 完全兑现 companion_secondary_p02_shot |

Frame 01: PASS
Frame 02: PASS
Frame 03: PASS
Frame 04: PASS
Frame 05: PASS

## 8. 结论

V22 从零到 Visual Lock 测试图的完整链路（Story → Character → Environment → Visual Narrative → Resolved Frame Contract → 生成）可执行、门禁自检全过、五张测试图达到"普通年轻人在经历这件事时手机相册会留下的照片"的目标质感：真实摄影叙事明显强于 V2.1 的通用风格图批次（Camera Authorship / 逐帧环境 / 正常底片前置）。

测试范围口径重申：本 pilot 为 Delegated 层测试证据，未跑正式四门禁 Visual Lock / Production / Release；F01/F04 的 POV 构图偏差作为已知问题记录，进入正式批次前需在 prompt 层修复或人工确认。

---

**V22_PRODUCTION_PILOT_RESULT: PASS**

测试资产路径：
- 测试图（评审对象）：`episodes/11_仲夏夜惊魂/V22_PILOT_TEST/media/v22-pilot/out/01-05.png`
- 原始生成：`episodes/11_仲夏夜惊魂/V22_PILOT_TEST/media/raw/`
- 生成提示词：`episodes/11_仲夏夜惊魂/V22_PILOT_TEST/prompts/production/01-05.txt`
- 20 帧 Resolved Frame Contract：`episodes/11_仲夏夜惊魂/V22_PILOT_TEST/meta/runtime/contracts/frames/`
- Story / Storyboard：`episodes/11_仲夏夜惊魂/V22_PILOT_TEST/story/`
- 机器状态与门禁：`episodes/11_仲夏夜惊魂/V22_PILOT_TEST/meta/episode-state.json`、`meta/story-gates.json`（`current_state=IDEA_LOCKED`，未推进正式 stage）

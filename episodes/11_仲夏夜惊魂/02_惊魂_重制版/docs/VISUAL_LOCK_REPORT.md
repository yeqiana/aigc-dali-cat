# VISUAL LOCK REPORT - 仲夏夜惊魂（V2.2.1 重制版）

Episode：`episodes/11_仲夏夜惊魂/01_惊魂`

阶段：Visual Lock（四帧验证，非正式 Production）

日期：2026-09-03

结论：四帧方向性验证通过，记录生产返修项；等待用户显式授权进入 Production。未生成 20 帧正式图，未修改 Story Lock / Character / Environment / Visual Narrative 前期资产，未提交 Git。

## 1. 执行前检查

机器验证全部 PASS，无 SHA / Authority 漂移：

```text
CHARACTER CONTRACT VERIFIED              # character_contract.py validate --require-locked
VERIFIED                                 # character_visual_contract.py validate
CHARACTER APPEARANCE ANCHOR VERIFIED     # character_appearance_anchor.py verify
WORLD IDENTITY CONTRACT VERIFIED         # story_world_identity.py verify
ENVIRONMENT CONTRACT VERIFIED            # environment_contract.py verify
VISUAL NARRATIVE CORE VERIFIED mode=production frames=20 authority=PREPRODUCTION_DERIVED_CONTRACT
V2.2.1 PREIMAGE READINESS PASS | world_identity=PASS character_anchor=PASS visual_narrative=PASS
```

- P01 主角身份：已锁定（25 岁普通中国年轻男性，白色短袖+浅色牛仔裤+深色运动鞋，第一人称主摄影不出镜）。
- P02 妹妹身份：已锁定（20 岁老家妹妹，浅色短袖+牛仔短裤+平底凉鞋基线；不是解释者、不是剧情工具人）。
- Appearance Anchor：有效（`same_person_across_frames=true`）。
- 世界环境：有效（`CN_MAINLAND_YOUNG_ADULT_DEFAULT_V1`，中国大陆南方丘陵村庄夏夜）。
- 20 Frame Narrative：已锁定（schema 2，frames=20，无静默反转与最后照片揭秘设计）。
- 未出现 `HANDOFF_SHA_MISMATCH`。

机器链缺口（非画面问题，记录不伪造）：`frame_contract.py compile-all` 报 `manifest.artifacts.storyboard missing`。本集未建立 storyboard 工件，因此 Resolved Frame Contract 无法机器编译；四张验证帧由 Visual Lock 独立通道生成并做镜检，不能把本报告当作 Frame Contract 已编译的证据。

## 2. 四帧交付

全部输出 4:5（1080×1350），保存在 `episodes/11_仲夏夜惊魂/01_惊魂/media/visual-lock/calibration/`（media 目录被 `.gitignore` 忽略，不提交 Git）。

| Frame | 角色 | 文件 | SHA-256 |
| --- | --- | --- | --- |
| 01 | ordinary baseline | `01_ordinary_baseline.png` | `3c0092e778c4e09bb42f58b4f5aab31ecdf38854faa2a6048a9a59c1fe18b64f` |
| 08 | first anomaly | `08_first_anomaly.png` | `b9bfa756c933ee2dc3efe9b1e66e2e38f6f30dff27660cd5a4d122bed7416155` |
| 15 | high-impact escalation | `15_high_impact.png` | `9a3e23caca6ccc3787e81e794dc52427aa602f115ad436521c2d256bab3d11c8` |
| 20 | ending atmosphere | `20_ending_atmosphere.png` | `7c0212ec4b00d057651a7e04f8ba30624a6ae1d935d8e3ad4d3f637eab7910fe` |

## 3. 逐帧检查

### Frame 01 - ordinary baseline

- Story Purpose：普通生活真实性。P01 夏夜回老家村口，妹妹在路灯下小跑过来准备上车；手机相册第一张的随手拍。
- Continuity Check：P02 黑色中长发扎低马尾、浅色短袖上衣、浅蓝牛仔短裤、平底凉鞋基线成立；同夜同人锚点用于 Frame 08/20 的人物一致性参照。
- Visual Risk Check：无恐怖元素、无异常暗示、无电影构图；村口路灯、水泥村道、红砖墙、黑色踏板电动车符合大陆村镇夏夜。P02 上衣实测为米白/浅黄系、短裤为浅米牛仔，与「浅蓝色牛仔短裤」文字基线存在色相偏差，列入生产返修项。
- 判定：PASS（方向性）。

### Frame 08 - first anomaly

- Story Purpose：第一次轻微异常。妹妹闻声从门里出来，两人说起巷口路灯；第一眼正常，第二眼注意到远处孤零零亮着的歪杆路灯。
- Continuity Check：妹妹不解释、不指认、无夸张反应（转身回望、姿态自然）；门灯暖光、红砖院墙、门口台阶与 Frame 20 同院落环境一致。
- Visual Risk Check：无鬼、无怪物、无字幕解释；异常保持未知。P02 服装与 Frame 01 同夜同人但生成时出现浅色运动鞋与米白上衣偏差，未严格锁死平底凉鞋与浅蓝牛仔短裤，列入生产返修项（正式 Production 必须以 Frame 01 服装基线为准）。
- 判定：PASS（方向性，含返修项）。

### Frame 15 - high-impact emotional escalation

- Story Purpose：情绪最高点之前。走熟的路变成陌生下坡机耕道，车灯照出长下坡与落灰三轮车；熟悉感失效、空间错位，但不升级为恐怖片。
- Continuity Check：第一人称越车把视角成立（画面下缘只带到车把与手/衣摆局部），P02 坐身后不需正面出现；与 Frame 17 循环参照的乡村机耕道环境一致。
- Visual Risk Check：无鬼脸、无人脸异常、无血腥；下坡纵深与三轮车尺度参照清楚。画面内三轮车出现可辨识的物理车体字样（DAYANG），属中国农用车辆真实符号，但与本帧"画面不出现文字"的镜检口径有冲突，列入生产返修项（建议弱化或改角度规避）。
- 判定：PASS（方向性，含返修项）。

### Frame 20 - ending atmosphere

- Story Purpose：最终余味。不知怎么走回自家老屋院门口，妹妹在门灯下回头笑了一下，回到日常夏夜：堂屋灯正常、台阶上蒙着纱罩的绿豆汤碗；异常不解释、不反转。
- Continuity Check：妹妹低马尾、浅色短袖、牛仔短裤、平底凉鞋同夜同人；门灯暖光、红砖院墙、竹椅与电扇一角与 E1/E3 老屋环境一致。
- Visual Risk Check：遵守四项禁止规则：
  1. 无最后一张照片揭示异常；
  2. 无手机回放/回看机制；
  3. 无相册反转；
  4. 无静默反转（画面落在人物行动与情绪释放后的真实余味）。
  画面无任何文字、水印、拍摄界面。
- 判定：PASS。

## 4. 摄影规格

四帧均为竖幅普通智能手机夜拍观感：高 ISO 噪点、夜景 HDR、门灯/路灯暖光轻微过曝、暗部扎实、轻微手持晃动、取景随意，符合"像真实手机相册随手拍"的 Visual Lock 目标；无电影感构图、无专业灯光、无恐怖片镜头语言。

## 5. 进入 Production 前待办

1. 补齐 storyboard 工件（或按 V2.2.1 主链建立 storyboard + Resolved Frame Contract），解除 `frame_contract` 机器链缺口。
2. 正式 20 帧以 Frame 01 为 P02 服装基线（浅色短袖+浅蓝牛仔短裤+平底凉鞋）统一再生成，覆盖 Frame 08/15 已记录的返修项。
3. Frame 15 车体字样弱化或改角度规避。
4. 最终像素终审由用户多模态人工确认，机器不替代人工亲眼审核。

## 6. 最终状态

- 四帧 Visual Lock 验证帧：已生成并完成机器验证与方向性自审。
- `meta/episode-state.json` 维持 `IDEA_LOCKED`：官方状态机（七阶段）不存在 `VISUAL_LOCK_PASS`，正向推进只能经 `episode_state.py transition` 相邻前进；本集尚未建立 storyboard 工件，无法通过 `STORYBOARD_LOCKED` 门禁。本报告不越级改写唯一机器阶段事实源。
- 状态：Visual Lock 验证帧完成，等待 storyboard 工件补齐并授权进入 Production；不生成 20 帧正式图。
- 未提交 Git、未 Push。

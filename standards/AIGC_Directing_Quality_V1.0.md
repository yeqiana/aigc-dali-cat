# Story OS V2.1｜AIGC Directing Quality Contract V1.0

> 本规范是 Story OS V2.1 的质量增强 Contract，不新增 Episode Stage。

## 1. Capture Event Contract
每张正式图在写提示词前必须回答：
- 谁在拍；
- 为什么偏偏此刻会拍；
- 设备在哪里；
- 被摄对象是否意识到镜头；
- 拍摄者此刻的身体/心理状态；
- 真实机位限制；
- 为什么这张会被保留下来；
- 最多 1–2 个由现场物理造成的成像缺陷。

真实性来自拍摄行为与物理因果，不来自统一噪点、滤镜、污渍。

## 2. Storyboard Information Density
逐图执行删图测试。删除后若对因果、证据、悬念、空间理解、人物状态均无损失，则该帧为 REDUNDANT_FRAME。
连续 5 帧必须至少有一次强进展；连续 BRIDGE 不超过 2 帧；同构图/同动作且无新信息不超过 2 帧。

## 3. Voice Contract
声音卡是 Story Authority。至少固定：
人物、角色、知识边界、讲述原因、此刻已知/未知、紧张时语言变化、恐惧时语言变化、禁止无来源技术词。
字幕继续执行 48 字上限、连续三图、朗读测试、删字幕测试。

## 4. Persistent World State
前期建立 initial_state，并为每帧记录 delta。
人物在场状态、服装、伤势、设备、拍摄者发生敏感变化时，必须有 story_event。
每帧 Resolved Frame Contract 绑定该帧 effective world-state SHA。

## 5. Non-destructive Asset Lineage
所有新候选和返修图只追加版本，不覆盖历史：
Frame NN v1 → v2 → v3，记录 parent SHA、Frame Contract SHA、触发原因和 scheduler item。

## 6. Golden Episode Regression
Golden Set 是人工挑选的代表剧集，不自动把所有旧项目当金标准。
建议至少覆盖：2004–2010、2020s、手机 POV、老数码设备、西北农村、雨夜、炎热、山路、巨大异常、室内异常、4–5 人群像。
回归工具只负责机器可验证指标；最终视觉水平仍由真实 Pixel Review/人工或模型 Critic 负责。

## 兼容原则
- 不新增 Episode Stage。
- 老 Episode 不自动迁移。
- 新 CREATIVE_STORY 运行时自动 enable `meta/directing-quality.json`。
- 已锁定老 Episode 若未 enable，可继续现有 Handoff / image_continue。
- 新 Handoff 在 Directing Quality enabled 时，必须冻结 Voice / Density / Capture Event / World State Authority SHA。

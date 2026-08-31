# Story OS V2.1 Character & Entry Pool Contract V1.0

## 核心原则

先决定“几个什么样的普通年轻人为什么会来到这里”，再决定“他们碰上什么不可思议的东西”。

人物与进入异常的方式要生活化；异常本身可以非常大胆。

## 默认人物母池

- **2004–2010**：19–25 岁，中心 20–23 岁；普通男生、女生、2–3 人朋友组、4–5 人男女混合朋友团。
- **2020 年代**：22–28 岁，中心 24–25 岁；普通男生、女生、两人朋友/情侣、4–5 人朋友团、生活化工作/课题/科考小组。

第一人称 POV 也必须固定大概人物形象：年龄、性别、衣着、设备、体型，以及同伴成员锚点。

## 进入异常的生活化动机

旅行、自驾、回老家、朋友聚会、打游戏、喝酒、挑战、废弃游乐园/旧学校/烂尾楼、露营、徒步、生活化出差、采风、实习、课题组、青年科考、偶然绕路。

工作/科考只解释“为什么来到这里”，不能成为专业解决异常的功能。

## 默认禁用主角

抢修员、电工、维修工、检修员、警察、刑警、记者、调查员、侦探、专业探灵人、特工、秘密异常研究员、官方异常调查组。

这些专业人物可以作为背景/配角，但不能作为默认主角发动机。

## NO-ANOMALY TEST

Story Lock 前把异常全部删掉，问：

> 如果什么怪事都没有发生，这几个年轻人的这一天仍然像真实生活吗？

必须 PASS，并在最终 Story 完成后显式写入 `rechecked_against_final_story=true`。

## 机器链路

```text
Runtime Request
→ Character Pool / Entry Pool / Scene Pool
→ meta/character-contract.json (DRAFT)
→ Concept Divergence
→ Concept Ambition
→ Story Build
→ NO-ANOMALY TEST
→ Character Contract LOCKED
→ Story Critic
→ STORYBOARD_LOCKED
→ Resolved Frame Contract 绑定 Character Contract SHA
→ Visual Lock / Batch
```

Character Contract 是 Story Build Input Contract，不新增 Episode Stage。

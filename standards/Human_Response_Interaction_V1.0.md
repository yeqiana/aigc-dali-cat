# Story OS V2.1｜Human Response & Interaction V1.0

> 目标：让人物真的生活在故事里，而不是站在异常旁边当比例尺。
> 本规则不新增 Episode Stage；字段直接进入 `meta/shot-progression-review.json`，并随 Resolved Frame Contract 进入生图 Prompt。

## 1. 情绪优先真实，不优先戏剧
每个有人物的 Frame 记录：
- `emotion.state`
- `emotion.intensity`：0–4
- `emotion.trigger`
- `emotion.response_sync`

推荐强度：
- 0 ordinary
- 1 relaxed / curious
- 2 alert
- 3 uneasy
- 4 urgent

默认禁止：
- 每张都张嘴瞪眼；
- 连续多张极端惊恐；
- 四个人同时做同一种恐怖片反应；
- 影视化走位、宣传照式情绪摆拍。

`intensity >= 2` 必须写真实触发原因。

## 2. 人物反应应当不同步
多人遇到异常时，更真实的是：
- 一个人先发现；
- 一个人继续看手机；
- 一个人已经开始收东西；
- 一个人还没完全反应过来。

允许 `asynchronous`、`shared_but_unsynchronized`；不允许 theatrical synchronized reaction。

## 3. Meaningful Interaction
互动不是每张都谈恋爱，而是人与人真实地共同经历事件，例如：
- 车内/景点自拍；
- 后排朋友抢镜、有人系安全带；
- 递手机给同伴看；
- 指向远处异常；
- 一起看地图；
- 递水/递东西；
- 帮忙拉冲锋衣、压帽子、整理背包；
- 拉住袖子提醒；
- 催人上车；
- 一起收拾东西；
- 一个人上车后回头叫其他人。

多人故事中，任意连续 5 个“有人物 Frame”至少应有 1 个 meaningful interaction。
但总体互动不应超过约 75%，避免变成情侣写真/旅游广告。

## 4. Opening Social Anchor
图 01/02 的合照不能只是所有人整齐正视镜头。
至少一张存在自然关系互动，例如：
- 拿手机的人距离镜头更近；
- 一人靠近、一人抢镜；
- 有人没完全看镜头；
- 有人正在系安全带/整理背包；
- 朋友做轻微手势或说话。

先像真实朋友出游相册，再像角色定妆照。

## 5. Wardrobe 可以参与动作
服装不只是静态造型：
- 风大：压帽子、拉兜帽；
- 降温：拉冲锋衣拉链；
- 下雨：递伞、收湿外套；
- 高海拔：整理保暖帽、背包肩带；
- 民宿/低海拔换轻装后：一起看路线、吃东西、收行李。

互动必须由天气、活动、关系或异常推动，不能为“画面好看”硬摆动作。

## 6. 与 Human Action Ladder 的关系
Emotion = 人现在是什么感受。
Interaction = 人与谁/什么发生关系。
Human Action Stage = 人下一步做什么。

三者必须因果一致：
`notice → verify → discuss → move → act → fail/adapt → consequence`
而不是 `站着看 → 站着看 → 站着看`。

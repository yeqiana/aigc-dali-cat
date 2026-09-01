# Story OS V2.2.6｜全局第一人称随手拍 Capture Grammar

## 核心规则

从本版开始，所有 Episode、所有 Visual Profile 默认叠加：

`FIRST_PERSON_CASUAL_SNAPSHOT_V1`

默认拍摄语法：

- 摄影者属于事件现场；
- 第一人称或同行者持机视角；
- 私人记录 / 随手拍；
- 非摆拍；
- 构图允许不完整、轻微偏斜、遮挡；
- 人物不必看镜头；
- 可自然出现手、肩膀、车门、门框等前景；
- 禁止全知第三人称、导演式站位、三人整齐排队、海报式构图。

## Visual Profile 与 Capture Grammar 分工

Visual Profile：
- 年代
- 色彩
- 胶片 / 数码质感
- 光线
- 皮肤和材质
- 环境视觉语言

Capture Grammar：
- 谁在拍
- 从哪里拍
- 是否摆拍
- 构图行为
- 摄影者是否真实存在于现场

当两者冲突时：

**Capture Grammar 的构图与摄影者语法优先。**

因此即使某个 Profile 里存在：

`composition=film_framing`

也不能再把默认画面变成全知第三人称电影剧照。

## 自拍

自拍不是默认。

只有 Story / Frame Contract 明确要求自拍时才使用自拍构图。

## 查看某一 Episode 实际 Capture Grammar

```bat
python -X utf8 scripts/story_capture_grammar.py show "<episode>"
```

## 显式覆盖

如未来某一集确实需要监控、无人机、固定机位等特殊语法，可在：

`<episode>/meta/capture-grammar.json`

建立显式 override。没有 override 时全部回到第一人称随手拍默认。

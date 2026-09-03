# M00｜现实生活纪实母版 V2.0

> 英文辅助名：Reality-First Everyday Documentary Master。
> Story OS 默认视觉母风格（M00）；MP4、网吧、流水席、误入小镇保留为校准来源，不再作为 M00 正式名称。
> **用户未明确指定其他画风/质感时，默认使用本风格。**
> 本文只统一视觉语言，不强制统一年代、设备、场景或剧情套路；具体采集设备和时代物理表现优先。

## 1. 一句话定义

> 像一个普通人真的去过那个地方，用当时合理的设备顺手拍下生活，异常只是慢慢侵入这些本来很普通的照片。

关键词不是“复古滤镜”，而是：

**真实中国生活空间 + 私人相册/旧数码记录习惯 + 现场光 + 不完美抓拍 + 非电影化 + 异常从现实里长出来。**

### 1.1 M00 机器参数

机器权威文件：`standards/visual_profiles/M00_MP4_网吧_流水席_旧数码.json`。路径为兼容旧 Episode 保持不变，正式名称以文件内 `profile_name=现实生活纪实母版` 为准。

| 参数 | 值 | 级别 |
|---|---|---|
| profile_id | M00 | 固定 |
| profile_name | 现实生活纪实母版 | 固定 |
| reality_first | true | 硬规则 |
| ordinary_chinese_life_density | high | 硬规则 |
| composition | unposed_imperfect_personal_record | 硬规则 |
| people | ordinary_unprepared_not_actor_like | 硬规则 |
| subject_awareness | mostly_unaware_or_natural | 默认 |
| practical_available_light | true | 硬规则 |
| cinematic_lighting | forbidden_by_default | 硬规则 |
| commercial_hdr | forbidden | 硬规则 |
| portrait_bokeh | not_default | 默认 |
| camera_perfection | not_default | 默认 |
| hero_shot | not_default | 默认 |
| symmetrical_composition | not_default | 默认 |
| beautification | forbidden | 硬规则 |
| skin_rendering | natural | 硬规则 |
| color | environment_driven_low_to_medium_saturation | 硬规则 |
| global_vintage_lut | forbidden | 硬规则 |
| cinematic_color_grading | forbidden_by_default | 硬规则 |
| white_balance | environment_driven | 默认 |
| contrast | natural_device_limited | 默认 |
| dynamic_range | device_and_scene_driven | 默认 |
| texture | causal_controlled_imperfection | 硬规则 |
| noise | device_environment_driven | 默认 |
| motion_blur | cause_required | 硬规则 |
| lens_artifacts | cause_required | 硬规则 |
| scene_cleaning | forbidden_by_default | 硬规则 |
| life_clutter | preserve | 硬规则 |
| environment_imperfection | preserve | 默认 |
| visual_polish_ceiling | documentary_realism | 硬规则 |
| anomaly | embedded_in_reality_before_spectacle | 硬规则 |
| anomaly_environment_binding | required | 硬规则 |
| spectacle_first | forbidden_by_default | 硬规则 |
| scale_reference | required_for_large_anomaly | 硬规则 |
| screen_ui_physics | required_when_present | 硬规则 |
| camera_authorship | required | 硬规则 |
| ghost_camera | forbidden | 硬规则 |
| capture_reason | required | 硬规则 |
| save_reason | required | 默认 |
| narrative_information_gain | required_after_frame_01 | 硬规则 |
| narrative_redundancy | forbidden_by_default | 硬规则 |
| continuity | strict | 硬规则 |
| reference_assets | preferred_when_identity_matters | 默认 |
| seed_dependency | none | 固定 |

## 2. 默认路由

当用户没有指定画风时：

`M00｜现实生活纪实母版`

优先级：

1. 用户明确指定的单集/系列视觉体系；
2. 本集年代、地点、拍摄者、实际采集设备的物理真实性；
3. M00 的视觉语言。

因此：

- 2026 年手机故事可以使用 M00，但不能伪造成 2007 年低分辨率手机；
- 2000s 卡片机 / DV / 旧手机可以自然继承旧数码的动态范围、低照度、压缩、对焦等缺陷；
- “旧数码感”必须由设备和现场产生，不能统一套颗粒、漏光、暗角或脏黄 LUT。

## 3. 四个校准来源

### F01｜流水席

继承：

- 中国乡镇/村落真实生活密度；
- 人群不是群演站位；
- 暖光、裸灯、临时棚、饭桌杂物都来自现场；
- 异常藏在人群秩序和生活细节里。

### F02｜MP4

继承：

- 旧数码物件的时代可信度；
- 私人记录和翻拍屏幕的真实缺陷；
- 小道具推动故事，而不是做“宝物特效”；
- 压缩、边缘软、屏幕溢出等必须有物理原因。

### F03｜误入小镇

继承：

- 县城/小镇空间的普通感；
- 走路、回头、临时停下拍照形成的非标准构图；
- 第一眼先像真实地点，第二眼才发现规则不对。

### F04｜网吧

继承：

- 廉价室内数码质感；
- 日光灯、屏幕光、局部暗区、混合色温；
- 老网吧/普通网吧的桌椅、线材、墙面、键鼠和杂物密度；
- 弱光时允许噪点、对焦犹豫、运动拖影，但禁止统一“恐怖压黑”。

> F04 是用户在 V1.8 明确指定的校准组成。当前若仓库没有正式锁定资产，不伪造 source SHA；未来可补登记，不影响其作为默认视觉语义锚点。

## 4. 必须保留的视觉 DNA

- **现实先于异常**：没有异常时，这张图也应该像正常相册。
- **生活杂物不要清场**：保留合理但与剧情无关的东西。
- **现场光**：自然光、日光灯、裸灯泡、屏幕光、路灯等可解释光源。
- **非电影化**：不要英雄低机位、轮廓光、青橙调色、商业 HDR、统一浅景深。
- **人物像普通人**：背影、侧身、被遮挡、做自己的事，不要每个人都看镜头。
- **构图像记录**：偏位、裁一点、略歪、前景遮挡、临时抓拍都可以。
- **缺陷必须有因果**：走路才有方向性糊，弱光才有噪点/慢快门，翻拍屏幕才有反光/摩尔纹。
- **异常嵌进现实**：先小矛盾、再第二证据、再影响现实行为，不默认突然巨怪/鬼脸/超自然光。

## 5. 现代设备如何继承 M00

M00 不是“旧画质滤镜”。

如果剧情明确使用 2020s 手机：

- 保留现代手机合理的分辨率、自动曝光和动态范围；
- 但禁止商业摄影式精修、过度 HDR、假电影布光、过度人像虚化；
- 仍使用随手记录构图、真实生活杂物、现场光和异常侵入逻辑；
- 不为了“风格统一”强行加低清、旧 JPEG、CCD 色偏。

## 6. 防止账号视觉同质化

**锁质感，不锁场景。**

M00 不要求每篇都出现：

- MP4；
- 网吧；
- CRT；
- 土路；
- 老房；
- 塑料凳；
- 流水席。

这些是校准来源，不是必须复用的视觉道具。

真正统一的是：

> 现实密度、拍摄行为、现场光、设备物理成立、人物不表演、异常从日常中侵入。

题材、地点、异常机制、核心道具、中段升级和高潮仍必须按“四把锁 / 最近5篇账号级同质化”主动变化。

## 7. 单集显式覆盖

需要换风格时，在 `meta/story-gates.json` 登记：

```json
{
  "visual_profile": {
    "mode": "override",
    "profile_id": "...",
    "profile_path": "standards/visual_profiles/....json",
    "capture_profile": "auto",
    "override_reason": "本集为什么不走默认 M00"
  }
}
```

如果没有该字段，或 `mode=default`，Story OS V1.8 自动解析为 M00。

## 8. 与 Visual Lock 的关系

Visual Lock 时必须把“解析后的视觉 Profile 文件”一起 SHA 锁定。

这样可以保证：

- 你批准的是哪套主画风有证据；
- 后续批量生成时不能悄悄换视觉母版；
- 设备/年代仍由真实性卡和 capture profile 决定，不被 M00 越权覆盖。

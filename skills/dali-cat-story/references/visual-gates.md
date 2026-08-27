# Visual Gates

## 发布资产硬规则

按照当前主规范，正式图文默认：

- 9:16 原生
- 1080×1920
- 无黑边 / 白边 / 留白

validator 会检查可解析 PNG/JPEG 的尺寸。非正式发布辅助资产不要放进 `paths.publish_dir`。

## 连续性锚点

建议在 `episode.yaml` 中记录：

```yaml
continuity:
  anchors:
    protagonist: protagonist_v1
    location: hometown_house_v2
    key_prop: mp4_black_v1
    wardrobe: black_jacket_v1
```

锚点不是提示词装饰，而是返修时的“不可无因漂移事实”。

## 四张视觉准入

`story.visual_admission_frames` 必须是 4 个互不重复、且落在总帧数范围内的图号。机器只检查数量/编号；多模态审核仍需判断：真实性、风格、异常可读性和批量扩展风险。

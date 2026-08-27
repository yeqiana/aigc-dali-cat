# Review & Release Gates

## 推荐 review 字段

```yaml
review:
  authenticity: pending
  continuity: pending
  subtitle: pending
  story: pending
  visual_admission: pending
  production: pending
  recommendation_fit: pending
  publish: pending
```

允许值：`pending / passed / failed / waived`。

`--release` 时，`review.release_required`（模板默认 8 项）必须全部为 `passed` 或有明确 `waived`；普通开发模式只检查字段是否合法，不强迫全部通过。

## 发布前机器门禁

- publish 目录存在。
- 发布图数量与 `format.frame_count` 一致。
- 01..N 连续，无重复图号。
- PNG/JPEG 尺寸符合 manifest。
- 字幕门禁通过（若 `subtitles.required: true`）。
- 锁定资产 hash 未变化。
- story/anti-homogeneity 的结构性硬门禁通过。

## 机器无法代替的终审

至少人工/多模态判断：

- 前 3/5/10 张是否真的有继续左滑欲望。
- 高潮图是否视觉上承担高潮，而非只在文案里说它是高潮。
- 终局是否重读前文/完成闭环。
- 人物、房屋、道具看起来是否真的是同一个。
- “真实手机相册感”是否物理成立，而不是滤镜模拟。

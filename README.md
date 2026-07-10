# 《啾啾和大力》AI 短视频资产库

本仓库用于管理《啾啾和大力》系列短视频的创作规范、视觉母版和单集交付资产。

## 目录说明

```text
assets/
  masters/images/       角色、场景、镜头和道具母版图片
docs/
  standards/            已锁定的生产规范
  drafts/               尚未锁定的工作草稿
  research/             外部作品与镜头语言研究
  masters/              母版资产清单与说明
episodes/
  giant-delivery-box/   《巨大快递盒》单集文档、关键帧和交付视频
```

## 当前资产

- 生产规范：尺寸比例、单集生产表、生成提示词与执行规范。
- 视觉母版：角色设定、世界观、空间、镜头和巨大物品比例参考图。
- 已交付单集：`episodes/giant-delivery-box/video/final.mp4`（9:16，约 15 秒）。

## 使用约定

1. `docs/standards/` 中的内容为当前锁定规范，修改前先复制到 `docs/drafts/` 迭代。
2. 新单集按 `episodes/<episode-slug>/` 创建，并将文档、关键帧和交付视频分别放入 `docs/`、`images/`、`video/`。
3. 母版图片统一放在 `assets/masters/images/`；对应说明文档放在 `docs/masters/`。
4. 所有素材均保留原始中文文件名，避免丢失创作语义。

# 《啾啾和大力》AI 短视频资产库

本仓库用于管理《啾啾和大力》系列短视频的当前生产规范、视觉母版、单集执行表和交付资产。

## 分支

- `main`：当前强节奏动画生产体系。
- `1.0`：旧版完整快照，冻结于提交 `a6f0f33`。

生产新内容只使用 `main`。需要查阅旧版规范时切换到 `1.0`，不在主分支复制旧文档。

## 当前执行入口

从[当前版本与执行入口](docs/standards/current/00_当前版本与执行入口.md)开始，依次使用：

1. [最终执行规范](docs/standards/current/01_最终执行规范.md)
2. [单集生产表](docs/standards/current/02_单集生产表.md)
3. [母版清单](docs/standards/current/03_母版清单.md)
4. [全量母版生成提示词](docs/standards/current/04_全量母版生成提示词.md)
5. [尺寸与比例规范](docs/standards/current/05_尺寸与比例规范.md)
6. [巨大物品选题库](docs/standards/current/06_巨大物品选题库.md)
7. [版本迁移说明](docs/standards/current/99_版本迁移说明.md)

## 目录

```text
assets/
  masters/              视觉母版及资产状态说明
docs/
  standards/current/    main 唯一生效的完整生产规范
  research/             外部作品与镜头语言研究
episodes/
  giant-delivery-box/   巨大快递盒复盘、重制执行表和旧版交付证据
```

## 当前生产方式

- 成片优先控制在 8–10 秒。
- 使用 4–6 个 1.3–2.5 秒短片段。
- 第一帧必须已经发生异常事件。
- 前 3 秒完成巨物、目标和冲突。
- 每个动作片段包含预备、爆发和结果。
- 角色使用动画电影头身、块状绒毛和夸张身体表演。
- 结尾包含第二次翻转或循环动作。

## 巨大快递盒

- [成片复盘 V1.0](episodes/giant-delivery-box/docs/啾啾和大力_巨大快递盒_成片复盘与改进建议_V1.0.md)
- [强节奏重制执行表 V1.1](episodes/giant-delivery-box/docs/啾啾和大力_巨大快递盒_强节奏重制执行表_V1.1.md)

现有 `video/final.mp4` 和关键帧是 1.0 交付证据，不代表 main 当前生产质量。

## 使用约定

1. 新单集复制 `docs/standards/current/02_单集生产表.md`，不要复制旧分支模板。
2. 单集按 `episodes/<episode-slug>/` 建立 `docs/`、`images/` 和 `video/`。
3. 新母版按全量母版提示词生成，通过 P0 验收后才能作为视频强参考。
4. 旧位图母版只参考身份、服装、比例和构图，不复制写实风格。
5. 所有规则修改先形成新版本并验证，不在多个文件中维护相互冲突的当前入口。

# Story OS V2.1｜Character Master Final Closure V1.0

本规范不增加 Episode Stage，只闭合 Visual Lock → Production → Final Snapshot 的人物身份链。

## 1. Visual Lock 必须真正执行 1+3

固定流程：

`ordinary_baseline 生成 → 单独 Pixel Review PASS → PROVISIONAL Master → 其余三张并行 → FOUR-admission Final Review → LOCKED Master`

依赖项不能因为 baseline “已经生成”就放行，必须因为 baseline “已经单独审核 PASS”才放行。

## 2. Baseline Review

`meta/visual-lock-baseline-review.json` 是 SHA-bound review evidence，不是新的 Story Authority。

必须绑定 baseline frame、image SHA、Frame Contract SHA、实际像素审核项；若为多人自拍，还需要核心人物 normalized face boxes。

## 3. Provisional / Locked Pixel Master

- baseline 单独 PASS：`meta/character-pixel-master.json.status = PROVISIONAL`
- 四项 Visual Lock 全 PASS：同一图片升级为 `LOCKED`
- Production 不使用 PROVISIONAL；只有 Visual Lock 后三张允许使用。

## 4. Derived Individual Crops

核心人物 crop 只能从已通过 baseline 的同一张群像照片确定性裁切：不重新生脸、不修改五官、不创建新身份；crop SHA 与源 master SHA 全部记录。

多人帧优先 Group Master；明确单人帧优先对应 individual crop。

## 5. Reference Arbitration

正式请求仍最多 2 个 reference：

- Visual Lock 后三张：baseline identity 必占 1 槽；
- Production 人物帧：identity + prop/location；
- 无人物帧：不浪费 identity 槽；
- setup/transition 更偏 location；
- evidence/reveal/climax/payoff 更偏 prop；
- capture_style 只在更高优先级 reference 不需要时使用。

## 6. Existing Episode Backfill

仅允许对 `VISUAL_CALIBRATED` / `PRODUCTION_PASSED` 做 derived backfill。
不得自动改动 `PUBLISH_READY` / `PUBLISHED` / `DATA_REVIEWED`，避免发布后证据漂移。

## 7. Final Candidate Snapshot

只要人物母版存在，就必须把以下内容直接锁进 Snapshot：

- `meta/character-pixel-master.json`
- Group Master 图片
- `meta/character-master-crops.json`
- 每张 individual crop 图片

任何 SHA 漂移都必须使 Snapshot 失效。

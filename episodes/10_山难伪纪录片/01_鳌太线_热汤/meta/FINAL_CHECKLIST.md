# FINAL CHECKLIST — generated evidence view

> 自动生成，只汇总现有状态/证据；**不是新的规范源，也不得保存 stage。**

- Episode: `episodes/10_山难伪纪录片/01_鳌太线_热汤`
- Generated: `2026-08-30T14:00:42`
- Current state: `PUBLISH_READY`
- Machine strict: `True`

## A. 机器事实

- ✅ `episode-state.json` 存在
- ✅ `story-gates.json` 存在
- ✅ `release-manifest.json` 存在
- ✅ strict 模式 production ledger 就绪
- ✅ story review passed
- ✅ visual admission passed
- ✅ authenticity passed
- ✅ production passed
- ✅ continuity passed
- ✅ publish review passed
- ⬜ Story Lock approval + SHA
- ⬜ Visual Lock approval + SHA
- ✅ Text Audit PASS
- ⬜ Release Package SHA locked

## B. Golden Path 锁点

- ✅ Story Lock：故事/专业分镜已锁
- ✅ Visual Lock：三张校准 + 四张视觉准入已锁
- ✅ Production Lock：批量生产与逐帧审核完成
- ✅ Release Lock：发布版本已锁

## C. 人工终审（必须人工回答）

- [ ] 第一眼像真实手机相册 / 合理采集设备，而不是电影剧照、概念图或商业摄影
- [ ] 拍摄者、设备、机位在物理上成立；第一视角设备没有无解释完整入镜
- [ ] 人物身份、服装、地点、关键道具、天气/时间线连续
- [ ] 前 5 张有继续滑动欲望，且每 3–5 张有新证据/因果/认知升级
- [ ] 高潮强于中段，并且不是最近作品的机制换皮
- [ ] 结尾回收前文线索，产生回看价值；没有多余尾图稀释高潮
- [ ] 字幕是人话，位置不压主体，不靠过上/过下/过右等违背本集锁定版式
- [ ] 封面、标题、简介、话题与最终成片一致，没有承诺画面里不存在的内容
- [ ] 若执行 subtitle_only / crop_only，锁定底图 hash 未变化

## D. 发布后闭环

- [ ] 已准备 6h / 24h / 48h / 7d 数据回填位置
- [ ] 下一篇选题会读取最近作品，检查题材、异常机制、场景语法、高潮与反转重复

## E. Validator 快照

- ✅ validate_episode.py --target PUBLISH_READY

```text
=== PASS D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\10_山难伪纪录片\01_鳌太线_热汤 ===
[PASS] clean
```
- ✅ machine_gate.py --target PUBLISH_READY

```text
=== PASS MACHINE GATE PUBLISH_READY :: D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\10_山难伪纪录片\01_鳌太线_热汤 ===
[PASS] clean
```

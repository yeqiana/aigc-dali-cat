# Dali Cat Story OS — START HERE V1.6

> 30 秒执行入口。这里不是第二套创作规范，只负责告诉 Agent **先读什么、现在在哪、下一步做什么**。
>
> 创作规则唯一权威：`standards/制作规范_正式版.md`  
> 阶段状态唯一事实源：`<episode>/meta/episode-state.json`

## 0. 黄金路径（Golden Path）

```text
恢复上下文
→ 选题 / 去同质化
→ 锁故事与专业分镜
→ 建真实性卡与连续性锚点
→ 三张真实性校准 + 四张视觉准入
→ Visual Lock
→ 批量生产
→ 逐帧审核 / 必要返修
→ Final Checklist
→ 发布
→ 6h / 24h / 48h / 7d 数据回填
```

机器状态仍只使用仓库原生七阶段：

```text
IDEA_LOCKED
→ STORYBOARD_LOCKED
→ VISUAL_CALIBRATED
→ PRODUCTION_PASSED
→ PUBLISH_READY
→ PUBLISHED
→ DATA_REVIEWED
```

**不要新建第二套 stage / status / workflow 状态。**

## 1. 每次任务只按这个顺序读

1. 本文件 `START_HERE.md`
2. 根目录 `SKILL.md`
3. 根目录 `AGENTS.md`
4. `standards/制作规范_正式版.md`
5. `standards/AUTHORITY_INDEX.json` 中与当前任务匹配的 active 从属细则
6. 目标剧集 README / docs / 锁定分镜
7. 目标剧集 `meta/episode-state.json`
8. 若 strict=true，再读 `story-gates.json / production-ledger.json / frame-reviews/`

不要为了“更保险”把整个 `standards/` 全部读一遍。旧版本和 superseded 文件只用于历史追溯。

## 2. 四个必须停下来的人工锁点

除非用户已经明确授权连续执行，否则以下节点必须显式确认后再继续：

1. **Story Lock**：故事与专业分镜是否锁定。
2. **Visual Lock**：三张真实性校准与四张视觉准入是否锁定。
3. **Repair Lock**：需要返修哪些图；未点名已通过帧不得连带重做。
4. **Release Lock**：标题、封面、字幕、简介、话题、发布图是否为最终版。

这四个锁点不是新状态机，只是人工决策 Gate。

## 3. Visual Baseline → Trial → Batch

所有新篇统一使用：

```text
人物 / 场景 / 设备真实性基线
→ 三张真实性校准
   A. 普通相册基线
   B. 最差但仍成立条件
   C. 首次重大异常
→ 四张视觉准入帧
→ VISUAL_CALIBRATED
→ 剩余图片批量生产
```

禁止“先把 20 张都出完，再回头找画风”。

## 4. 最小修改协议

用户说：

- “只改字幕 / 底图别动” → `subtitle_only`
- “只裁切” → `crop_only`
- “保持原画风重做这一张” → `regenerate_frame`
- “整段重做” → `regenerate_sequence`

未被点名的已通过帧默认锁定，不得顺手重做。

## 5. 一条命令知道下一步

```bash
python episodes/_system/story_os.py next <episode_dir>
```

仓库健康检查：

```bash
python episodes/_system/story_os.py doctor
```

生成最终验收清单：

```bash
python episodes/_system/story_os.py checklist <episode_dir>
```

只看状态，不修改：

```bash
python episodes/_system/story_os.py status <episode_dir>
```

## 6. 文档权威规则

`standards/AUTHORITY_INDEX.json` 只做路由，不创造规则：

- `canonical`：唯一主规范。
- `active_subordinate`：当前有效执行细则。
- `series_overlay`：系列覆盖层，只能补充，不得反向覆盖主规范硬规则。
- `reference`：参考材料，不是门禁。
- `superseded`：历史版本，默认禁止作为当前规则引用。

出现冲突：

```text
制作规范_正式版
> active subordinate
> series overlay
> reference
> superseded
```

## 7. Final QA 只生成，不再造第五套规范

`final_checklist.py` 只从现有状态、门禁和 manifest 汇总一份：

`<episode>/meta/FINAL_CHECKLIST.md`

它不是规范源，也不得保存 stage。最终人工仍需回答：

- 像不像真实手机相册 / 合理采集设备？
- 人物、地点、关键道具是否连续？
- 前 5 张有没有继续滑的欲望？
- 高潮是否足够强，且不是近期作品的重复机制？
- 结尾是否回收前文，并产生回看价值？
- 字幕是否像人话、位置是否压住主体？
- 封面 / 标题 / 简介 / 话题是否和成片一致？

## 8. 一句话原则

**规则可以很多，决策入口只能有一个。**

<!-- STORY_OS_V1_7_RELIABILITY_BEGIN -->
## 9. V1.7 生产可靠性

Golden Path 七阶段不变。V1.7 只在两个位置增加事务保护：

```text
Batch 生图请求
→ production_ledger begin
→ transport_guard preflight
→ 调用生图
→ success / technical failure

已锁图片只修文字
→ text_revision start
→ 编辑
→ diff + text_audit
→ submit
→ 用户明确批准 approve / 不满意 revert
```

技术失败不得消耗内容返修次数；技术重试不得改变请求指纹。文字专修不得触碰批准/发布图片、reference、release manifest、production ledger、episode state 或 story gates。
<!-- STORY_OS_V1_7_RELIABILITY_END -->

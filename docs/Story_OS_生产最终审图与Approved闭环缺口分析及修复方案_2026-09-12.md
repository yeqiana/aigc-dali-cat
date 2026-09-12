# Story OS 生产最终审图与 Approved 闭环缺口分析及修复方案

更新时间：2026-09-12

适用项目：Story OS V3

仓库：`D:\workspace\YeQianWorkSpace\yeqian\storyOS`

当前真实验收 Episode：`episodes/天界普通人的一天`

---

# 一、问题一句话说明

当前 Story OS 在“正式图片全部生成完成”之后，存在一个生产闭环缺口：

> 最终语义评审只接受已经进入 `approved_asset` 的图片，但图片要进入 `approved_asset` 又要求 Production Ledger 先把当前候选判定为 `PASSED`；现有 Fast Scout / Batch Review 都明确没有最终 PASS 权限，因此缺少一个真正负责“候选图最终审查并正式拍板”的收口步骤。

大白话：

```text
图片已经生成
↓
想做最终审图
↓
最终审图要求：先给我 approved_asset
↓
想生成 approved_asset
↓
Production Ledger 要求：这张图先 PASSED
↓
想标 PASSED
↓
现有快速审图/批次审图又明确不能授予最终 PASS
↓
没人能完成最后拍板
↓
流程卡住
```

这不是图片生成失败，也不是内容本身必然有问题，而是生产阶段缺少“候选图 → 正式通过 → approved_asset”的权威闭环。

---

# 二、当前实际流程与卡点

当前真实生产链已经运行到：

```text
故事锁定
↓
分镜锁定
↓
生图前编译
↓
视觉校准
↓
20 张正式图片生成
↓
快速像素审查 / 批次像素审查
↓
【当前闭环缺口】
↓
approved_asset
↓
全片最终语义评审
↓
生产正式通过
↓
字幕
↓
发布检查
↓
发布准备完成
```

其中：

- Fast Scout：只能做快速分流和早期发现明显问题，明确不是最终 PASS 权威。
- Production Batch Review：只能做批次实际像素的早期 repair barrier，明确不是最终 PASS 权威。
- `frame_semantic_review.py`：是真正的最终语义审查权威，但当前入口要求每帧已经存在 `approved_asset`，且 Ledger 状态已经进入 accepted states。
- `production_ledger.py promote`：又要求帧先处于 `PASSED`。

因此形成循环依赖。

---

# 三、相关现有模块职责

## 1. Fast Scout

文件：

`episodes/_system/fast_frame_scout.py`

职责：

- 快速发现明显坏图；
- 可输出 `PASS_FAST / REPAIR_NOW / DEFER_TO_FINAL`；
- `PASS_FAST` 只代表“暂时没有明显问题”；
- 不能作为最终 Production PASS。

结论：不能用 Fast Scout 直接批量把帧标记为 `PASSED`。

## 2. Batch Review

文件：

`episodes/_system/production_batch_review.py`

职责：

- 对一批真实图片做早期像素审查；
- 输出 `PASS_PREVIEW / REPAIR_NOW / UNCERTAIN`；
- 明确：`final_pass_authority = false`；
- `REPAIR_NOW` 可以提前触发返修；
- `PASS_PREVIEW` 不能授予最终 PASS。

结论：不能把 Batch Review 的 `PASS_PREVIEW` 当成 `production_ledger review --decision pass`。

## 3. Production Ledger

文件：

- `episodes/_system/production_ledger.py`
- `episodes/_system/production_ledger_run.py`
- `episodes/_system/production_ledger_manage.py`

关键状态链：

```text
ORIGINAL_READY / REPAIR_READY
↓ review pass
PASSED
↓ promote
approved_asset
↓ lock
LOCKED
```

限制：

- `review pass` 必须有真实内容审查依据；
- `promote` 只接受 `PASSED`；
- `lock` 只接受已有 `approved_asset`。

这个约束本身是正确的，不应放宽。

## 4. Frame Semantic Review

文件：

`episodes/_system/frame_semantic_review.py`

职责：

- 最终实际像素语义审查；
- 检查 Story Lock / Storyboard / Frame Contract / POV / 人物 / 连续性 / 异常可读性 / 信息增量 / 视觉叙事等；
- 是最适合承担“最终 PASS 权威”的模块。

当前限制：

`frame_records()` 只接受已经是 Production accepted state 且已经有 `approved_asset` 的帧。

也就是：

```text
最终评审入口要求 approved
但 approved 又需要最终评审结果
```

这是本次漏洞的核心。

---

# 四、为什么这是一个真实框架漏洞

这个问题不是某一期数据脏了，而是流程职责之间存在结构性空档。

Mock / 测试流程中，部分测试直接构造：

```text
PASSED / LOCKED
+
approved_asset
```

因此没有暴露真实生产中“谁负责把真实候选判为 PASSED”的问题。

真实生产第一次完整跑到这里后才暴露：

```text
真实候选
↓
Fast Scout / Batch Review 只能预审
↓
没有最终 PASS 权威执行入口
↓
Frame Semantic Review 又只审 approved_asset
```

因此它属于：

> 生产最终评审收口缺失 / Final Candidate Admission Gap

不是普通单帧 bug。

---

# 五、修复原则

修复必须遵守：

1. 不新增第二套状态机；
2. 不新增第二套 Production Ledger；
3. 不降低 Fast Scout / Batch Review 的权限边界；
4. 不允许把 `PASS_FAST` 或 `PASS_PREVIEW` 直接映射成最终 PASS；
5. 不允许为了推进流程手工批量把帧改成 PASSED；
6. 最终内容 PASS 仍由独立实际像素语义评审产生；
7. 继续复用现有 `production_ledger review / promote / lock`；
8. 返修仍遵守当前每帧内容返修预算；
9. 技术失败不消耗内容返修预算；
10. 所有最终通过必须有 SHA 绑定和 critic provenance。

---

# 六、推荐修复方案

核心思路：

> 不新建一个“Final Review 2”，而是扩展现有 `frame_semantic_review.py`，让它可以直接审当前 Production Candidate；审查通过后，再调用现有 Production Ledger 完成 `review pass → promote → lock`，最终继续使用 approved_asset 做全片绑定验证。

修复后的标准链路：

```text
正式候选图
↓
Frame Semantic Review（Candidate 模式）
↓
逐帧实际像素最终评审
├─ fail → CONTENT_FAILED / REPAIR
└─ pass
    ↓
    production_ledger review pass
    ↓
    PASSED
    ↓
    production_ledger promote
    ↓
    approved_asset
    ↓
    production_ledger lock
    ↓
    LOCKED
↓
全片 approved_asset 绑定复核
↓
Frame Semantic Review 全片连续性/去重/语义验证
↓
PRODUCTION_PASSED
```

这样最终权威仍只有一套：

`frame_semantic_review`

Ledger 仍然只是状态和证据执行层。

---

# 七、建议实施拆分

## P0：增加 Candidate Review 输入模式

修改：

`episodes/_system/frame_semantic_review.py`

新增候选收集逻辑，例如：

```text
candidate_frame_records()
```

读取：

`meta/production-ledger.json -> frames[NN].current_candidate`

只允许状态：

```text
ORIGINAL_READY
REPAIR_READY
```

要求：

- candidate 文件真实存在；
- SHA256 与 Ledger 一致；
- Frame Contract SHA 与生成尝试一致；
- Provider Receipt / generation evidence 可验证；
- 不允许读取已失效、superseded 或旧 attempt candidate。

## P0：Candidate 最终语义评审

对候选图运行现有 Hard Rules：

- scene_storyboard_fidelity
- story_beat_fidelity
- key_prop_fidelity
- character_identity
- wardrobe_continuity
- pov_photographer_legality
- spatial_continuity
- temporal_continuity
- anomaly_readability
- caption_image_support
- actual_information_gain
- environment_physics_fidelity
- anomaly_escalation_fidelity
- scale_reference_fidelity
- camera_authorship_physical
- moment_capture_credibility
- narrative_evidence_gain
- shot_grammar_diversity
- camera_defect_physics
- screen_content_physics
- visual_memory_continuity
- Directing V3 额外检查

不要降低标准。

## P0：逐帧收口

对于最终评审 `decision=pass` 的帧：

依次调用现有命令：

```text
production_ledger review --decision pass
production_ledger promote
production_ledger lock
```

注意：

- 不能直接编辑 production-ledger.json；
- 必须走现有命令/函数；
- approved_asset 的 source_sha256 必须绑定当前 candidate；
- lock SHA 必须等于 approved_asset SHA。

对于 `decision=fail`：

```text
production_ledger review --decision repair
↓
CONTENT_FAILED
↓
authorize-repair --delegated-auto
↓
Repair Queue
```

仅返修失败帧。

## P0：全片最终复核

所有帧都有 approved_asset 后，再运行当前完整的：

```text
frame_records()
perceptual_rows()
duplicate_pairs()
phase4_binding_errors()
verify_episode()
```

确保：

- 20/20 approved；
- 无近重复；
- 全片 Story / Storyboard / Frame Contract binding 正确；
- 人物/服装/空间/时间/POV/异常升级连续；
- critic provenance 有效；
- SHA 无漂移。

通过后才允许：

```text
VISUAL_CALIBRATED
→
PRODUCTION_PASSED
```

---

# 八、当前《天界普通人的一天》作为回归案例

当前真实状态可直接作为这次修复的验收样本。

已完成：

- 20 帧均有真实图片候选；
- Frame 15 已通过 crash recovery 正规恢复，没有重复生成；
- Frame 16 首版被真实像素审查判为明显失败：错误生成成拼贴海报；
- Frame 16 已走 delegated-auto 单次内容返修；
- Frame 16 新返修候选已经成功生成；
- 其余成功候选不得重生。

修复后应该从这里直接继续：

```text
现有 20 张 current_candidate
↓
Candidate Final Semantic Review
↓
仅失败帧返修
↓
pass 帧 review/pass/promote/lock
↓
20/20 approved_asset
↓
全片最终复核
↓
PRODUCTION_PASSED
```

禁止为了测试修复而重新生成全部 20 张。

---

# 九、验收标准

## 代码级

必须新增/补齐测试：

1. `ORIGINAL_READY` candidate 可以进入最终候选评审；
2. `REPAIR_READY` candidate 可以进入最终候选评审；
3. `TECH_FAILED / CONTENT_FAILED / NEEDS_USER` 不能被当作可审 candidate；
4. candidate SHA 漂移必须 fail closed；
5. Frame Contract SHA 漂移必须 fail closed；
6. pass 后必须真实执行 Ledger `review → promote → lock`；
7. fail 后只能进入 repair 路径，不能生成 approved_asset；
8. Fast Scout `PASS_FAST` 不能自动授予 PASS；
9. Batch Review `PASS_PREVIEW` 不能自动授予 PASS；
10. 全片 approved 后现有 `frame_semantic_review verify` 必须通过；
11. machine gate `PRODUCTION_PASSED` 必须通过；
12. 不允许通过直接 JSON 编辑绕开 Ledger。

## 真实 Episode 验收

`episodes/天界普通人的一天`：

```text
20 个正式帧
= 20 个 approved_asset
= 20 个有效 SHA binding
= 20 个最终语义 PASS
```

并且：

- Frame 16 必须使用返修后的新 candidate；
- 旧 Frame 16 拼贴图不能进入 approved；
- Frame 15 使用恢复出的原 Codex 产物，不重复生成；
- 无旧技术失败污染 next_action；
- 不重生已通过帧；
- 最终 `next_action` 能从 PRODUCTION 自动进入 RELEASE。

---

# 十、修复后的全自动目标

修复完成后，一句话生产应该可以连续执行：

```text
一句话需求
↓
故事锁定
↓
分镜锁定
↓
生图前编译
↓
视觉校准
↓
正式生图
↓
快速审查
↓
最终候选语义审查
↓
自动只返修失败帧
↓
正式通过并生成 approved_asset
↓
全片最终验证
↓
生产通过
↓
字幕
↓
发布门禁
↓
发布准备完成
```

中间不应该再因为“没人有资格把候选图最终判 PASS”而停住。

---

# 十一、明确不做的事情

本次修复不做：

- 不重构整个 Story OS；
- 不新建第二套 Review Engine；
- 不新建第二套 Ledger；
- 不修改 Episode 状态机；
- 不取消 approved_asset；
- 不把 Fast Scout 升级为最终权威；
- 不把 Batch Review 升级为最终权威；
- 不放宽 Production Machine Gate；
- 不允许自动接受明确失败图片；
- 不新增人工确认步骤；
- 不要求用户重新输入“继续”。

---

# 十二、最终结论

这个漏洞的本质不是“全自动偶尔停住”，而是：

> Story OS 已经具备图片生成、快速审查、返修和最终语义审查，但缺少把“真实候选图的最终语义结论”正式落到 Production Ledger，并生成 approved_asset 的桥梁。

最佳修复方式不是降低门禁，而是让现有 `frame_semantic_review` 真正承担最终 Candidate Admission Authority，并继续复用现有 Production Ledger 完成：

```text
candidate
→ final semantic review
→ PASSED
→ approved_asset
→ LOCKED
→ PRODUCTION_PASSED
```

修复后，该缺口应永久消失，并作为《天界普通人的一天》本次真实全流程验收暴露出的生产框架问题纳入回归测试。

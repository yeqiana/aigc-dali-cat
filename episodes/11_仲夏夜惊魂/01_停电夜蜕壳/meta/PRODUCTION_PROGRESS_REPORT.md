# 《停电夜蜕壳》生产进展与阻塞分析

> 快照时间：2026-08-31 22:30（Asia/Shanghai）  
> 剧集：`11_仲夏夜惊魂/01_停电夜蜕壳`  
> 当前机器阶段：`STORYBOARD_LOCKED`  
> 目标阶段：`PUBLISH_READY`

## 一、结论摘要

当前整体完成度建议按 **约 40%** 管理，不应按“已经生成 8 个图片文件”计算。

- 前期 Story、Storyboard、Character Contract、环境/影响合同和 20 帧 Frame Contract 已完成。
- Visual Lock 的 4 张准入图均已有当前候选，帧 08、17 已由用户直接接受为人工例外，四图已完成 SHA 绑定。
- 统一 Visual Lock Critic 尚未通过，原因不是画面内容被判失败，而是独立 worker 无法读取图片，正式错误为 `INPUT_IMAGES_UNAVAILABLE`。
- 20 帧中只有 4 帧有当前候选；3 帧为 `PASSED`，1 帧为 `ORIGINAL_READY`，16 帧尚未生成。
- `media/approved` 当前为 0 张，Production、Final Frame Review、字幕、简介、Release、Final Candidate Snapshot 均未完成。
- 四图绑定更新了 `story-gates.visual.calibration`，当前 handoff 再次出现 `HANDOFF_SHA_MISMATCH:meta/story-gates.json#stable_preproduction_subset`。Story、Storyboard、Character Contract 文件 SHA 未漂移，但按用户硬规则仍必须停止，不得继续批量生产。

## 二、已经花了多久

### 2.1 可观测总跨度

从机器状态记录的 2026-08-31 14:20，到 ledger 最近一次修复记录 22:30，可观测跨度约为：

**8 小时 10 分钟。**

这个数字包含前期审查、等待、用户决策、图片生成、返修、编码问题排查和审查环境故障，不等于模型持续运算了 8 小时。

### 2.2 分段耗时

| 时间段 | 约耗时 | 发生的工作 |
| --- | ---: | --- |
| 14:20–19:37 | 约 5 小时 17 分 | 前期门禁、Concept/Story/Recent-5 Critic、image_continue 激活准备 |
| 19:40–21:11 | 约 1 小时 31 分 | Visual Lock 四图生成、帧 01 技术重试、帧 08/17 两轮返修 |
| 21:11–22:30 | 约 1 小时 19 分 | 08/17 人工例外、handoff/合同重建、滚动审查与统一 Critic 排障 |

### 2.3 真正的图片后端耗时

Production Ledger 共记录 9 次生成尝试，其中 8 次产出图片、1 次技术失败。将每次 attempt 的开始与结束时间简单相加，图片后端累计约 **16 分 41 秒**；部分尝试并发执行，实际墙钟计算时间更短。

因此，本次“慢”的主要原因不是图片模型生成速度，而是：

1. 高风险帧内容返修；
2. 门禁状态和 SHA 绑定；
3. Windows/UTF-8/中文路径兼容问题；
4. 独立 Critic 无法获得视觉输入；
5. 人工例外缺少原生状态迁移，需要补齐审计路径。

## 三、当前进展与百分比

百分比有不同口径，不能混用。

### 3.1 机器阶段口径

发布前共有五个可见状态节点：

`IDEA_LOCKED → STORYBOARD_LOCKED → VISUAL_CALIBRATED → PRODUCTION_PASSED → PUBLISH_READY`

当前在第 2 个节点 `STORYBOARD_LOCKED`。按节点展示是 **2/5 = 40%**，但这只是阶段位置，不代表 40% 的媒体资产已经交付。

### 3.2 图片资产口径

| 指标 | 当前值 | 百分比 |
| --- | ---: | ---: |
| 有当前候选的帧 | 4/20 | 20% |
| Ledger 为 `PASSED` 的帧 | 3/20 | 15% |
| 可继续审查的 `ORIGINAL_READY` | 1/20 | 5% |
| 已提升到 `media/approved` | 0/20 | 0% |
| 尚未生成 | 16/20 | 80% |

当前 8 个图片文件包括旧候选和返修版本，不能按 8/20 计算进度。真正对应最终帧的当前候选只有 4 张。

### 3.3 工作包估算口径

为便于项目管理，按以下权重估算：

| 工作包 | 权重 | 当前完成估算 | 对总进度贡献 |
| --- | ---: | ---: | ---: |
| 前期与权威合同 | 30% | 100% | 30% |
| Visual Lock | 15% | 70% | 约 10.5% |
| 20 帧正式 Production | 30% | 15% | 约 4.5% |
| Rolling/Final Review 与返修 | 15% | 5% | 约 0.8% |
| 字幕、简介、Release、Snapshot | 10% | 0% | 0% |

加权结果约为 **45.8%**。考虑 Visual Lock 尚未取得有效 Critic PASS、approved 资产仍为 0，保守管理值取 **约 40%** 更诚实。

## 四、为什么生产这么费劲

### 4.1 必要的质量成本

这不是普通的“按提示词生成 20 张图”，而是要求每张图同时满足：

- 第一人称采集物理成立；
- 人物、衣着、地点、道具连续；
- 异常从小到大递进，并能无字幕读懂；
- 环境、光线、设备限制符合现实；
- 帧 08 的卷向和帧 17 的高冲击后果必须在像素中成立；
- 每张图片绑定当前 Frame Contract SHA；
- 通过 Rolling Review、Final Frame Review、近重复检查和 Release 门禁。

图片模型容易给出“视觉上很强”的结果，但不一定严格兑现指定动作、POV 或因果关系。帧 08、17 正是这种高风险帧，因此产生了原图、普通返修、用户例外返修三代候选。

### 4.2 可避免的工程成本

本次额外消耗主要来自 Story OS 工程链路尚未完全收敛：

- `image_continue` 要求 handoff Authority SHA 完全一致，但 Visual Lock 合法更新 `story-gates.visual.calibration` 后，又会改变 handoff 稳定子集 SHA，签名边界存在冲突。
- Ledger 原有“授权用户例外返修”，但没有“接受已生成例外候选”的合法命令。
- Visual Lock 绑定器原来只接受 queue `generated`，不接受已由用户明确批准、SHA 一致的 `scout_repair`。
- Windows `text=True` 使用活动代码页向 Codex stdin 编码，中文 Frame Contract 导致 `input is not valid UTF-8`。
- 中文绝对路径无法稳定传给视觉 sidecar，需要使用字节一致的 ASCII 临时附件。
- 独立 Codex worker 最终仍因 Windows sandbox `CreateProcessWithLogonW failed: 1385` 无法读取图片，统一 Critic 只能返回 `INPUT_IMAGES_UNAVAILABLE`。
- 旧失败传播逻辑曾把“图片输入不可用”误当内容失败，将帧 05 错误降级为 `CONTENT_FAILED`；现已恢复为 `ORIGINAL_READY` 并补上防护。

这些工程问题提高了审计可信度，但没有增加成片数量，是当前生产体感费劲的主要来源。

## 五、当前主要卡点

按优先级排列：

### P0：Handoff Authority SHA 再次不一致

当前验证结果：

```text
HANDOFF_SHA_MISMATCH:meta/story-gates.json#stable_preproduction_subset
```

已核验的冻结文件 SHA：

| 权威文件 | 当前 SHA-256 |
| --- | --- |
| `story/01_StoryLock.md` | `a0f7bb5ab9ad3931950a3d11ffc2b32e2d9b010f74f18ac2df838d84cfd97ba9` |
| `story/02_Storyboard.md` | `4677990eec404afa2b097201bb9aff253b104624c5eaf61e705792566d6919dd` |
| `meta/character-contract.json` | `fe128a1dcd3ccfd4d8458e2d01cbfef73f9c88d7c4adcdc3c85908df1e06874f` |

这说明前期故事和角色权威没有被偷偷重写；漂移来自 Visual Lock 绑定写入了 `story-gates.visual.calibration`。但在 handoff 规则调整或再次合规重建前，仍必须停止。

### P0：统一 Visual Lock Critic 无实际像素输入

正式证据：

```text
issue_codes = ["INPUT_IMAGES_UNAVAILABLE"]
summary.passed = false
Windows sandbox: CreateProcessWithLogonW failed: 1385
```

四帧已经完成绑定，但不能因为 08、17 获得人工例外就跳过统一 Critic。人工例外解决的是单帧处置，不等于四图整体 Visual Lock PASS。

### P1：正式 Production 尚未启动

- 16 帧仍为 `PENDING`；
- 4 张当前候选尚未全部进入 `media/approved`；
- `VISUAL_CALIBRATED` 尚未达到，不能启动剩余 Batch；
- 后续 Final Frame Review、字幕与 Release 都依赖 Production 完成。

### P1：运行时与状态迁移补丁尚需回归

本轮已补充：

- 直接用户接受现有例外候选；
- 只允许用户批准且 SHA 一致的 `scout_repair` 进入绑定；
- UTF-8 stdin；
- ASCII 临时图片附件；
- `INPUT_IMAGES_UNAVAILABLE` 不再污染 Ledger 内容状态；
- 恢复证据缺失导致的错误降级。

这些修改已通过 Python 编译、自测、Ledger Audit 和 `git diff --check`，但完整 V2.1 regression matrix 尚未执行。

## 六、剩余工作与时间预估

在两个 P0 卡点解决后，剩余工作为：

1. 重跑四帧统一 Visual Lock Critic并取得有效实际像素 PASS；
2. 推进 `VISUAL_CALIBRATED`；
3. 以最大 3 worker 生成剩余 16 帧；
4. Rolling Review、全帧 Final Critic、必要返修、近重复审计；
5. 将通过帧提升并锁定到 approved/publish；
6. 完成字幕、简介、话题、传播卡、Release Preflight；
7. 构建并验证 Final Candidate Snapshot；
8. 相邻推进到 `PRODUCTION_PASSED` 和 `PUBLISH_READY`。

基于现有单图生成约 2–3 分钟、最大 3 worker 的观测：

- 无新增内容返修的理想情况：约 **2.5–4.5 小时**；
- 有 3–6 张普通返修的现实情况：约 **4–8 小时**；
- 若独立视觉 worker/sandbox 继续不可用：无法给出完成时间，流程会持续卡在 Visual Lock。

以上是工程估算，不包含用户长时间离线等待，也不把后台模型等待冒充有效制作时间。

## 七、建议的最短恢复路径

1. 明确 handoff 稳定子集是否应排除 Visual Lock 运行态字段，或在不改 Story/Storyboard/Character 的前提下合规重建 handoff。
2. 修复独立 Critic 的 Windows 进程权限/视觉输入能力，确保四张附件能被实际读取。
3. 重跑 Visual Lock Critic，只有真实 PASS 后才推进状态。
4. 启动 16 帧 Batch，后续按现有连续执行授权自动完成 review、字幕、Release 和 Snapshot。

## 八、当前可确认事实

- Story、Storyboard、Character Contract 没有被重写。
- 帧 08 r2 与帧 17 r2 均有用户直接接受记录和 SHA 绑定。
- 四帧 Visual Lock 已绑定，但统一 Critic 没有看到图片，因此没有通过。
- 当前阶段仍是 `STORYBOARD_LOCKED`。
- 当前整体完成度按管理口径约 40%。
- 当前最主要的瓶颈是 handoff 签名边界和独立视觉审查运行时，不是图片模型生成速度。

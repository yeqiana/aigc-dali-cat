# EP003 Production Exposure Audit

日期：2026-09-11

Episode：10_彼此的天上 / EP003（雾中的另一座生活区）

审计目标：仅审计，不修改代码。

---

# 1. 暴露问题列表

|编号|问题|等级|是否已有规则|是否需要修复|
|-|-|-|-|-|
|E001|Frame01 身份锚存在，但生产执行链仍存在 reference 注入与 provider 执行结果不完全绑定风险|P0|已有视觉锚、Character Contract、Gate规则|需要修复|
|E002|Gate 主要验证配置/evidence 存在，不能完全证明 provider 实际使用了指定身份 reference|P0|已有 gate 体系|需要修复|
|E003|Story Lock 对剧情约束存在，但从 Story Contract 到 Frame Contract 的语义强绑定不足，部分反转依赖人工理解|P1|已有 Story Lock|需要增强|
|E004|EP003 生产过程中出现大量候选图/返修尝试，说明自动挑选与早期失败隔离仍不足|P1|已有 Scheduler/Review/Repair|需要优化|
|E005|M00 默认视觉执行成功，但真实手机相册感、人物稳定性仍依赖 prompt 强约束|P1|已有 M00 规范|需要增强|
|E006|新增视觉模式扩展方向正确，但视觉模式治理不足时可能导致账号统一风格漂移|P2|部分已有规范|需要补充|
|E007|Runtime 已具备 workflow/scheduler/gate/review/release 链路，但证据闭环仍偏文件存在性验证|P0|已有 Runtime 设计|需要增强|

---

# 2. 根因分析

## A. 制作问题

EP003 暴露的主要不是人工制作失误，而是从“能生产”进入“稳定批量生产”阶段后的系统问题。

表现：

- Frame01、角色、场景均有设计，但后续帧仍可能出现人物漂移。
- 生产过程中需要多轮人工判断哪些图是真正符合故事的。
- 20帧完成不代表20帧都来自同一个稳定生产约束。

结论：

制作流程已经超过纯人工阶段，需要进一步强化机器验证。

---

## B. Prompt问题

存在问题：

- Prompt 已包含身份、设备、环境描述。
- 但是 Prompt 本身不是强制执行机制。
- 当 provider 生成偏差时，没有足够强的自动拒绝能力。

根因：

Prompt 负责表达意图，不负责保证结果。

---

## C. Story Lock问题

EP003 Story Lock 基本成立：

- 人物关系明确。
- 第一人称视角明确。
- 异常递进明确。

但暴露：

故事一句话设定与20张图片之间缺少机器级语义验证。

尤其：

- 前期铺垫是否服务最终反转。
- 最后一张情绪是否达到预期。
- 人物关系是否闭环。

目前仍依赖 Review。

---

## D. Runtime问题

已有能力：

- workflow
- scheduler
- gate
- review
- repair
- release

均存在。

暴露问题：

Runtime 更像“流程编排系统”，还不是完全意义上的“生产质量控制系统”。

缺口：

1. provider receipt 与视觉结果绑定不足。
2. reference 使用真实性验证不足。
3. gate 对执行事实验证弱于配置验证。

---

## E. Gate缺陷

最大问题：

Gate 可以回答：

“有没有配置身份锚？”

但不能完全回答：

“这张图生成时真的用了这个身份锚，并且结果保持一致吗？”

这是 EP003 最大系统暴露。

---

# 3. 是否进入暴露清单

|问题|判断|
|-|-|
|E001 身份锚执行链问题|升级已有 W-17|
|E002 Gate配置通过但执行未知|新增 W-21：Reference Execution Evidence 缺失|
|E003 Story Lock 到 Frame Contract 语义断层|新增 W-22：Story Semantic Trace 不完整|
|E004 生产候选与失败隔离|已有 Runtime Scheduler 优化项，不新增|
|E005 M00真实性依赖Prompt|已有真实性规范，不新增|
|E006 多视觉模式治理|新增 W-23：Visual Profile Governance|
|E007 Runtime Evidence闭环|升级 Runtime Gate 类问题|

---

# 4. EP004之前必须修复项

## P0

### 1. 身份锚执行验证（W-17升级）

目标：

不是检查 reference 文件存在，而是检查：

Frame Contract → Reference → Provider Request → Generation Receipt → Output Review

完整链路。

---

### 2. Gate 从配置验证升级为执行验证（W-21）

必须增加：

- reference 使用证据
- provider receipt关联
- frame级视觉一致性结果

---

## P1

### 3. Story Lock 到 Frame Contract 语义链增强（W-22）

目标：

让机器知道：

第1张为什么存在，第10张承担什么，第19张为什么高潮，第20张为什么收尾。

---

### 4. Visual Profile治理（W-23）

新增画风前必须定义：

- 适用账号定位
- 与M00关系
- 是否影响真实照片感

---

# 总结

EP003 暴露的核心不是“不能生产”，而是：

Story OS 已经从 V2.7 图片生产工具进入 V3 生产系统阶段。

当前最大短板：

> 生产链路能证明“流程执行过”，但还不能完全证明“生成结果符合约束”。

EP004 前重点不是增加功能，而是补齐：

身份执行证据 + Gate真实性验证 + Story语义闭环。

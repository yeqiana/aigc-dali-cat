# Story OS V3 Production Exposure Multi Issue Repair Plan

更新时间：2026-09-12

目标：

针对 EP003 生产暴露问题，以及 V3 改造过程中累计暴露漏洞，整理一次性批量修复方案。

本次目标不是继续增加流程，而是把 Story OS 从“可生产”提升到“稳定批量生产”。

---

# 一、当前暴露问题总览

|编号|问题|等级|影响|修复方向|
|-|-|-|-|-|
|E001|身份锚声明与实际图片生成引用绑定不足|P0|人物连续性无法完全保证|建立 Reference Execution Receipt|
|E002|Gate 验证配置存在，无法证明 Provider 真正使用|P0|可能出现假通过|增加执行事实校验|
|E003|Story Lock 到 Frame Contract 语义链弱|P1|图片满足场景但削弱故事反转|增加 Story DNA Trace|
|E004|大量候选图和返修没有形成经验闭环|P1|生产成本增加|增强失败分类与学习|
|E005|M00真实感依赖 Prompt|P1|真实手机照片稳定性不足|增加视觉结果评分|
|E006|视觉模式扩展缺少治理|P2|账号风格可能漂移|增加 Style Registry|
|E007|Evidence 偏文件存在验证|P0|无法证明真实生产过程|升级 Evidence Gate|

---

# 二、本轮批量修复原则

## 不做

- 不重新设计 Phase10 企业能力。
- 不增加新的状态机。
- 不推翻现有 Workflow / Runtime DAG。
- 不重新制作已有 Episode。

## 做

- 强化生产事实链。
- 强化机器验证。
- 增加失败学习。
- 增加跨 Episode 复用能力。

---

# 三、第一批 P0 修复（必须优先）

## 1. Reference Execution Binding

目标：解决 E001/E002。

新增能力：

```
Frame Contract
      ↓
Reference Requirement
      ↓
Generation Request
      ↓
Provider Receipt
      ↓
Generated Asset
      ↓
Verification
```

要求：

- 每张关键帧保存实际 reference 输入记录。
- Provider 返回结果必须绑定 request id。
- Gate 不再只检查 required reference 是否存在。
- Gate 必须检查 execution evidence。

验收：

可以回答：

“这张图片为什么认为人物身份正确？”

---

# 四、第二批 P1 修复

## 2. Story DNA Trace

解决 E003。

增加：

```
Story Intent
 ↓
Story Beat
 ↓
Frame Contract
 ↓
Visual Evidence
```

每帧增加：

- 服务剧情目标。
- 情绪目标。
- 反转贡献。

避免：

图片很好看，但与故事无关。

---

## 3. Production Failure Learning

解决 E004。

失败分类：

- identity_failure
- composition_failure
- story_failure
- realism_failure
- provider_failure
- review_failure

进入：

```
Production
 ↓
Failure Record
 ↓
Pattern Learning
 ↓
下一集预防规则
```

---

## 4. Visual Reality Score

解决 E005。

新增检查：

- 手机拍摄感。
- 光线真实性。
- 人物自然程度。
- 非AI感。
- 场景连续性。

Prompt 不再承担全部责任。

---

# 五、第二阶段治理

## Style Registry

解决 E006。

建立：

```
Style ID
 ↓
视觉规则
 ↓
适用题材
 ↓
禁止事项
```

M00 保留为默认母版。

新增风格必须注册，不允许自由扩散。

---

# 六、Evidence Gate 升级

解决 E007。

当前：

```
配置存在 = PASS
```

升级：

```
配置存在
+
执行记录存在
+
资产绑定存在
+
验证通过
=
PASS
```

---

# 七、实施顺序

## Batch 1（最高优先级）

1. Reference Execution Receipt
2. Provider Evidence Binding
3. Evidence Gate 强化
4. EP003问题回归测试

## Batch 2

1. Story DNA Trace
2. Failure Learning Loop
3. Visual Reality Score

## Batch 3

1. Style Registry
2. 长期账号学习系统增强

---

# 八、最终目标

修复后生产链：

```
一句话需求
 ↓
Story OS Runtime
 ↓
Story Lock
 ↓
Frame Contract
 ↓
Reference Binding
 ↓
Image Production
 ↓
Evidence Verification
 ↓
Learning Loop
 ↓
下一集自动优化
```

最终达到：

不是“能生成20张图片”，而是“稳定生成符合账号规律的20张故事图片”。

---

# 九、2026-09-12 Production Hardening 验收状态

| 编号 | 状态 | 已验证的闭环 |
|---|---|---|
| E001 | DONE | Frame Contract 的参考要求写入 Generation Attempt；Provider Receipt、参考 SHA 与资产候选必须匹配。 |
| E002 | DONE | `machine_gate.py` 不再以“required reference 文件存在”判定成功；缺 receipt、未验证、锚点/哈希漂移均为 FAIL。 |
| E003 | DONE | `story_dna_trace.py` 生成 Story Intent/Beat/Frame Contract 映射；逐帧 Contract 绑定且核心 required frames 未覆盖时阻断 `PUBLISH_READY`。 |
| E004 | DONE | `failure_memory.py` 只接受受控失败分类，Repair Task 要求在实际终态调用 `record_repair_outcome`；编排启动时读取历史经验，计划阶段不伪造结果。 |
| E005 | DONE | `visual_reality_score.py` 提供六维图片真实性评分入口；低分进入现有 Repair 路径，不替代人工审核。 |
| E006 | DONE | `standards/style-registry.json` 注册 M00、古风、天界日常、旧 DV，并映射既有 Visual Profile Registry 的执行权威。 |
| E007 | DONE | 证据门禁要求执行记录、provider receipt、资产/锚点绑定和 verified 结果，不把文件存在视为生产成功。 |

## 修改文件

`episodes/_system/story_dna_trace.py`、`failure_memory.py`、`visual_reality_score.py`、`style_registry.py`、`frame_contract.py`、`machine_gate.py`、`incremental_frame_review.py`、`production_orchestrator.py`、`repair_engine.py`、`standards/style-registry.json`、`tests/system/test_v3_production_hardening.py`、`reports/EP003_Production_Hardening_Report_20260912.md`。

## 测试证据

- `pytest tests/system/test_v3_production_hardening.py -v`：5 passed。
- `pytest tests/system/test_reference_execution_evidence.py -v`：18 passed。
- `pytest tests/system/test_story_semantic_trace.py -v`：26 passed。

## EP003 回归

归档对象 `episodes/_archive/20260911_EP003_abandoned_雾中的另一座生活区` 只读验证结果为：Story DNA、Visual Reality Score、Reference Execution Receipt 均缺失；机器门禁另报告历史媒体/语义评审缺失。结果为 `Historical Evidence Missing`/FAIL，不补写任何 approval、Gate PASS 或 episode state。W-17 由 receipt 锚点与哈希漂移用例覆盖，W-20 保持既有真实错误分类链，W-21 缺 receipt 明确 FAIL。

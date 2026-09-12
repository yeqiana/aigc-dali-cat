# Story OS Repair Budget Exceeded 返修额度耗尽治理方案 V1.0

更新时间：2026-09-12

## 一、背景

EP003「天界普通人的一天」全流程生产过程中发现：

单个 Frame 在内容审核失败后，如果自动返修额度耗尽，当前流程容易将 Frame 失败升级为 Episode 阻塞。

当前逻辑倾向：

```
Frame失败
 ↓
尝试Repair
 ↓
额度耗尽
 ↓
Episode停止
```

该行为不符合生产系统设计。

Story OS 应允许局部资产问题存在，不应该因为单帧失败破坏整个生产连续性。

---

## 二、问题定义

### 当前问题

返修额度表示：

> 自动修复能力已经达到限制。

但当前容易被解释为：

> 整个生产失败。

两者不是同一个概念。

---

## 三、核心原则

### Frame 生命周期与 Episode 生命周期分离

Frame:

```
GENERATED
 ↓
REVIEW_FAILED
 ↓
REPAIRING
 ↓
REPAIR_BUDGET_EXCEEDED
```

Episode:

```
继续生产
 ↓
收集所有Frame结果
 ↓
最终Gate判断是否发布
```

---

## 四、新状态设计

新增：

```
REPAIR_BUDGET_EXCEEDED
```

含义：

- 自动返修次数已经达到限制
- 当前Frame无法继续自动修复
- 不是技术异常
- 不是Episode失败

示例：

```json
{
  "frame_id": "Frame03",
  "repair_state": "REPAIR_BUDGET_EXCEEDED",
  "attempts": 2,
  "budget": 2,
  "next_action": "CONTINUE_PIPELINE"
}
```

---

## 五、后续治理方向

1. Frame级状态增加额度耗尽状态。
2. Production Ledger记录真实原因。
3. next_action不因单Frame额度耗尽停止整个Episode。
4. PUBLISH_READY Gate统一判断：
   - 是否允许发布
   - 是否需要人工介入
   - 是否需要重新生产

---

## 六、风险

如果不修复：

- 后续EP004/EP005仍可能因为单图问题卡死。
- 自动生产稳定性无法提升。
- 人工介入点不可控。

---

## 七、实施前置

本文件仅为分析方案，不修改Runtime行为。

后续实施：

1. 状态模型调整
2. Ledger适配
3. Repair Engine调整
4. Gate验证
5. 增量复审联动

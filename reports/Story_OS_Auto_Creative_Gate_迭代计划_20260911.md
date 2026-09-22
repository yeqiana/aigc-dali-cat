# Story OS Auto Creative Gate 迭代计划

日期：2026-09-11

## 背景问题

EP003 生产验证发现：当前 Runtime 已经具备自动执行能力，但在 STORYBOARD_LOCKED → VISUAL_CALIBRATED 阶段仍需要宿主动作。

当前流程：

```
STORYBOARD_LOCKED
        ↓
HOST_ACTION_REQUIRED
        ↓
人工确认 Visual Lock
        ↓
Production
```

问题：

用户期望：一句话输入后，系统可以自主完成故事生产。

当前实现：

- 图片生成自动化 ✅
- 图片失败恢复自动化 ✅
- Batch 调度自动化 ✅
- 额度治理自动化 ✅
- 创作决策自动化 ❌

## 目标

新增 Auto Creative Gate，使 Story OS 支持可配置的自主生产模式。

目标流程：

```
STORYBOARD_LOCKED
        ↓
AUTO VISUAL LOCK
        ↓
Critic 自动评分
        ↓
选择 baseline / worst / anomaly / high-impact
        ↓
VISUAL_CALIBRATED
        ↓
Production Wave
```

## 设计原则

1. 不替代人工审核模式。
2. 增加 production_mode 配置。
3. SAFE 模式保持当前严格 Gate。
4. AUTO_PRODUCTION 模式允许 Agent 自主推进。
5. 所有自动决策必须留下 evidence。

## 迭代计划

### Phase 1：Production Mode

新增：

```
production_mode:
  safe
  auto_production
```

### Phase 2：Auto Visual Lock

能力：

- 自动生成 4 类校准图
- baseline
- worst condition
- first anomaly
- high-impact admission

### Phase 3：Auto Critic Decision

能力：

- 自动评分
- 自动选择最佳方案
- 生成 decision evidence

### Phase 4：Runtime Integration

接入：

```
STORYBOARD_LOCKED
↓
Auto Creative Gate
↓
VISUAL_CALIBRATED
```

## 当前优先级

P1：EP003 不阻塞，继续使用当前 Gate。

P2：EP003 完成后实施 Auto Creative Gate。

原因：

当前生产稳定性问题（W-05/W-06）已经修复，继续生产优先验证图片生产闭环。

## 验收标准

完成后：

```
一句话需求
 ↓
Story OS
 ↓
Story Lock
 ↓
Visual Lock
 ↓
20 Frame Production
 ↓
Release
```

中间无需人工推进阶段，只保留最终验收入口。

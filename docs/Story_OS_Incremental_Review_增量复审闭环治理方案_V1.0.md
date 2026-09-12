# Story OS Incremental Review 增量复审闭环治理方案 V1.0

更新时间：2026-09-12

## 一、背景

EP003生产过程中发现：

正常流程：

```
Production
 ↓
Final Review
 ↓
Repair
 ↓
Review
```

但是当用户主动要求例外返修时，缺少标准化重新进入审核链路的机制。

---

## 二、问题定义

当前缺口：

```
用户例外返修
 ↓
生成新图片
 ↓
缺少标准Review入口
```

导致：

- 新资产可能没有完整证据链。
- Gate状态可能与实际资产不一致。
- 发布判断依赖人工记忆。

---

## 三、核心原则

返修不是重新生产Episode。

应该：

```
原Frame Contract
        |
        ↓
新Asset Attempt
        |
        ↓
Incremental Review
        |
        ↓
更新Frame Evidence
        |
        ↓
重新计算Gate
```

---

## 四、增量复审模型

新增概念：

```
Review Attempt
```

每次图片变化都产生独立审核记录。

示例：

```json
{
  "frame_id": "Frame05",
  "attempt": 3,
  "review_type": "incremental_review",
  "source_asset_sha": "xxx",
  "decision": "PASS"
}
```

---

## 五、治理目标

1. 用户返修可以安全进入生产链。
2. 不污染历史Review结果。
3. 保留完整资产演进记录。
4. Gate始终基于最新有效证据。

---

## 六、实施方向

后续实施：

1. 增加Incremental Review入口。
2. 绑定Frame Contract SHA。
3. 更新Ledger与Evidence。
4. 防止旧Review覆盖新结果。
5. 与Release Gate联动。

---

## 七、当前状态

本文为分析方案。

暂不修改Runtime代码。

待 Repair Budget治理完成后统一实施。

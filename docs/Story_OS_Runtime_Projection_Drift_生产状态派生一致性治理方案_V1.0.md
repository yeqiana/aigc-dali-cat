# Story OS Runtime Projection Drift 生产状态派生一致性治理方案 V1.0

更新时间：
2026-09-12


## 一、问题背景

在「天界普通人的一天」全流程生产过程中发现：

实际生产资产状态、Production Ledger、Runtime Next Action 三者出现不一致。

表现：

```
media/approved
    ↓
实际已有大量已审核资产

production-ledger
    ↓
记录部分生产事实

next-action.json
    ↓
仍判断 GENERATE_IMAGES
```

导致 Runtime 派生动作与真实生产状态不一致。


---

## 二、问题现象

当前案例：

Episode:

```
天界普通人的一天
```

实际：

- 01-20 图片生产基本完成
- approved 目录存在最终资产
- 已进入终审收敛阶段

但是：

```
meta/runtime/next-action.json

action:
GENERATE_IMAGES
```

仍认为存在待生产 Frame。


---

## 三、根因分析

### 根因1：派生状态优先级错误

当前链路：

```
Runtime
 ↓
生成 next-action
 ↓
驱动执行
```

但是正确关系应该：

```
Canonical Evidence
        ↓
Production Ledger
        ↓
Runtime Projection
        ↓
Next Action
```

Runtime 只能解释事实，不能创造事实。


---

## 四、核心原则

### 1. Runtime Projection 不是状态源

以下仍然保持唯一权威：

```
meta/episode-state.json
```

以及：

```
production-ledger.json
release-manifest.json
frame review evidence
```


### 2. Next Action 必须基于最新事实计算

禁止：

```
旧 next-action
      ↓
继续执行
```

必须：

```
重新 reconcile
      ↓
重新生成 next-action
```


---

## 五、目标状态模型

```
Asset Evidence
      |
      v
Production Ledger
      |
      v
Reconciliation
      |
      v
Runtime Projection
      |
      v
Next Action
```


---

## 六、需要增加的治理能力

### 1. Production Reconciliation

每次恢复生产前执行：

检查：

- approved 数量
- review 状态
- ledger 状态
- repair 状态
- release 状态

输出真实生产快照。


### 2. Projection Version

Runtime 派生文件增加：

```
source_digest
projection_time
```

避免读取旧状态。


### 3. Action 防误执行

执行前必须验证：

```
next_action
      |
      v
current evidence
```

如果不一致：

```
RECONCILE_REQUIRED
```

而不是继续执行旧动作。


---

## 七、与当前漏洞关系

该问题连接：

1. 终审结果未回写 Ledger
2. interrupted_unknown 污染 next_action
3. Repair Budget Exceeded
4. Incremental Review Closure

共同目标：

让 Story OS 从“流程驱动”升级为“事实驱动”。


---

## 八、实施顺序

1. 增加 reconciliation 分析
2. 修正 next-action 生成逻辑
3. 增加 projection 校验
4. 增加测试覆盖
5. 接入生产恢复流程


## 九、结论

Story OS 不应该相信上一次运行留下的动作。

应该始终根据最新生产事实决定下一步。

历史状态用于审计。
当前证据决定行动。

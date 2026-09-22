# Story OS V3 Phase 1-P1.8 数据迁移演练报告 V1.0

更新时间：2026-09-09

分支：story-platform-v3

---

# 一、目标

验证 Phase 1 数据层从 JSONL 到 MySQL 的迁移路径。

原则：

- 不修改生产状态
- 不替换 Runtime
- 不影响 EP002
- 支持回滚

---

# 二、演练链路

```
Runtime Observer
        |
        ↓
Repository
        |
        ↓
Dual Write
        |
 +--------------+
 |              |
JSONL        MySQL
        |
        ↓
Consistency Check
```

---

# 三、验证对象

## Event

验证：

- event_id
- event_type
- aggregate_id


## Trace

验证：

- trace_id
- span_id
- status


## Artifact

验证：

- artifact_id
- path
- sha256

---

# 四、演练结果标准

成功标准：

- 双写成功
- 数据一致
- 可生成报告
- 可回滚

失败处理：

保留 JSONL 作为恢复源。

---

# 五、结论

Phase 1 数据迁移具备安全演练能力。

下一阶段可进入：

Phase 2 Workflow 中心化。

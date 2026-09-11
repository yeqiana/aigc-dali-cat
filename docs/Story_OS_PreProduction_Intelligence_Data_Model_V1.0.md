# Story OS PreProduction Intelligence Data Model V1.0

更新时间：2026-09-11

状态：Design Only（方案设计，不进入代码实施）

---

# 一、设计目标

定义 Pre Production Intelligence MVP 的核心数据对象。

原则：

- 数据服务于 Advisor
- 不新增第二状态机
- 不替代 Story Lock
- 不替代 Memory System

---

# 二、核心数据关系

```
Story Lock
    |
    ↓
Story DNA
    |
    ↓
Similarity Evidence
    |
    ↓
Advisor Report
    |
    ↓
Review Report
    |
    ↓
Memory Reference
```

---

# 三、Story DNA Entity

用途：

故事结构指纹。

示例：

```yaml
story_id:
setting:
relationship:
character:
anomaly:
emotion:
narrative:
visual_pattern:
```

特点：

- 描述故事
- 不评价故事
- 可用于历史比较

---

# 四、Similarity Evidence Entity

用途：

保存风险判断依据。

结构：

```yaml
evidence_id:
current_story_id:
related_episode_id:
risk_type:
risk_level:
matched_features:
explanation:
```

要求：

任何 HIGH 风险必须存在 Evidence。

---

# 五、Advisor Report Entity

用途：

保存 Advisor 输出。

结构：

```yaml
report_id:
episode_id:
decision:
risks:
recommendations:
confidence:
created_time:
```

decision：

```
PASS
WARNING
NEEDS_REVISION
```

---

# 六、Review Report Entity

用途：

记录创作者最终选择。

结构：

```yaml
review_id:
advisor_report_id:
creator_decision:
final_result:
feedback:
```

说明：

Advisor 建议与 Creator 决策分离。

---

# 七、Memory Reference Entity

用途：

连接 Experience Store。

保存：

- 历史案例引用
- 生产结果
- 反馈数据

不保存：

- 硬规则
- 固定评分

---

# 八、MVP 数据边界

第一阶段只需要支持：

1. Story DNA 创建
2. 历史 Episode 查询
3. Similarity Evidence 保存
4. Advisor Report 生成
5. Review 反馈回流

---

# 九、明确非目标

暂不设计：

- 自动训练模型
- 自动修改故事
- 自动生产决策
- 复杂知识图谱

---

# 十、后续演进

未来可扩展：

```
Experience Store
        ↓
Pattern Learning
        ↓
Advisor Capability Evolution
```

# Story OS V3 Phase10-P10.2 Quota & Metering 详细设计 V1.0

更新时间：2026-09-11

项目：Story OS

分支：story-platform-v3

---

## 一、目标

把 Phase 6.6 的 quota_policy / quota_usage 设计落地为运行时资源计量，为限流与计费提供统一计数基础。核心原则：计量只负责「数数」，不负责「记账」（记账归 P10.3），并且计量失败不阻断业务主流程。

---

## 二、现状

- Phase 6.6 已设计：quota_policy（限制定义）+ quota_usage（使用记录）。
- platform/ 后端当前无 quota 模块。
- 现有图片生成（image scheduler，max workers 3）、Agent 执行、Workflow run、Token 消耗都有运行事实，但无配额计量。

---

## 三、配额维度与资源类型

资源类型枚举：

- IMAGE_GENERATION（图片生成张数）
- AGENT_EXECUTION（Agent 执行次数）
- WORKFLOW_RUN（Workflow 运行次数）
- TOKEN（模型 Token 消耗）
- STORAGE（存储字节 / 对象数）

配额层级：

- tenant 级：租户总配额
- user 级：个人配额

周期：daily / monthly / total（累计）。

---

## 四、数据模型

- quota_policy（id, tenant_id, resource_type, period, limit_value, status, created_time, updated_time）
- quota_usage（id, tenant_id, user_id, resource_type, period_key, used_value, updated_time）

约束：

- period_key 由 resource_type + period + 周期窗口确定（如 IMAGE_GENERATION:2026-09-11），保证幂等归并。
- quota_usage 用（tenant_id, user_id, resource_type, period_key）唯一键，配合 UPSERT 原子累加。

---

## 五、计量流程

    运行时埋点
      ↓
    原子累加（Redis INCR + MySQL UPSERT）
      ↓
    超限判断（used >= limit）
      ↓
    拦截或放行

埋点位置：

- 图片生成：image scheduler 每次出图 / 重试计数
- Agent 执行：agent runtime 每次 execution
- Workflow：workflow run 每次
- Token：模型调用回执累计
- 存储：artifact 写入字节数

---

## 六、原子性与一致性

- 并发计数用 Redis 原子 INCR，避免重复计数；MySQL 持久化用 UPSERT 归并。
- 周期窗口切换时以 period_key 隔离，不跨周期串数。
- 计量失败降级为「放行 + 告警」，不阻断生产（fail-open）。

---

## 七、与现有 platform/ 集成

- platform/quota/（新增：policy、usage、meter、checker）
- 埋点接入：platform/agent/runtime、image scheduler、workflow、repository（存储）
- 与 P10.3 Billing 解耦：quota 只产出计数事实，billing 再据此记账。

---

## 八、验收标准

- 配额超限被拦截（tenant 级与 user 级分别生效）。
- 并发下计数不重复、不丢失（Redis INCR + UPSERT 幂等验证）。
- 现有生产不回归（tests/platform + tests/system 全绿）。

---

## 九、风险

- 计量失败不应阻断业务：fail-open + 告警，不能因 Redis 抖动导致生产中断。
- 计数原子性依赖 Redis，需定义 Redis 不可用时的降级路径（本地计数 + 延迟回补）。
- Token 计量口径需与模型回执对齐，避免估算与真实用量漂移。

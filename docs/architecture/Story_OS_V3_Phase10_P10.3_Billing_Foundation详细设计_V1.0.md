# Story OS V3 Phase10-P10.3 Billing Foundation 详细设计 V1.0

更新时间：2026-09-11

项目：Story OS

分支：story-platform-v3

---

## 一、目标

把 Phase 6.6 的 Billing 预留（subscription / plan / billing_record）落地为记账基础。核心原则：只做「记账预留」，与支付解耦，不实现支付网关。

---

## 二、现状

- Phase 6.6 已预留 subscription / plan / billing_record，未来支持 Free / Pro / Enterprise。
- platform/ 后端当前无 billing 模块。
- P10.2 配额计量已设计（待落地），billing 消费其计数事实，自身不重复计数。

---

## 三、计费模型

    plan（Free / Pro / Enterprise）
      ↓
    subscription（tenant 订阅）
      ↓
    billing_record（周期账单）

plan 定义价格与配额包；subscription 绑定 tenant 与 plan；billing_record 记录周期用量与金额。

---

## 四、数据模型

- plan（id, plan_code, plan_name, billing_cycle, price, quota_config, status）
- subscription（id, tenant_id, plan_id, status, current_period_start, current_period_end, created_time）
- billing_record（id, tenant_id, subscription_id, period_key, usage_summary, amount, status, created_time）

约束：

- quota_config 与 P10.2 的 quota_policy 对齐（plan 级配额包）。
- billing_record 的 period_key 与 quota_usage 的 period_key 同口径，便于对账。

---

## 五、状态机

subscription 状态：

- PENDING（待生效）
- ACTIVE（生效中）
- PAST_DUE（欠费）
- CANCELED（已取消）

billing_record 状态：

- DRAFT（草稿）
- ISSUED（已出账）
- PAID（已支付）
- VOID（作废）

---

## 六、与 P10.2 的关系

    quota_usage（周期计数事实）
      ↓
    周期末聚合
      ↓
    billing_record 生成（usage_summary + amount）

金额计算：plan 单价 × 用量；超额部分按 plan 定义的超额单价计。

---

## 七、与支付解耦

- 不实现支付网关、不接入任何支付渠道。
- 只做记账预留：记录金额与状态；支付结果通过预留的回调接口写入（后续接入时再实现）。
- PAID / PAST_DUE 状态只由外部支付事件驱动，不由本模块凭空判定。

---

## 八、与现有 platform/ 集成

- platform/billing/（新增：plan、subscription、record、state）
- 消费 platform/quota/ 的 usage 事实，与 platform/tenant/（P10.1）的租户绑定。

---

## 九、验收标准

- 周期末能从 quota_usage 聚合生成 billing_record。
- subscription 状态机迁移正确，非法迁移被拒绝。
- 全程无支付依赖，模块可离线运行。

---

## 十、风险

- 金额计算口径必须与 quota 对齐，避免对账漂移。
- 支付属合规敏感，本阶段只预留接口，不实现任何真实资金流转。

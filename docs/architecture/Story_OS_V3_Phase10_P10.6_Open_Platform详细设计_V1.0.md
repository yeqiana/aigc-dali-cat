# Story OS V3 Phase10-P10.6 Open Platform / External API 详细设计 V1.0

更新时间：2026-09-11

项目：Story OS

分支：story-platform-v3

---

## 一、目标

把 Phase 5 的内部 Platform API 演进为开放平台，支持外部系统安全接入。核心原则：复用已有 Controller / Route / ServicePort，只在其前加「鉴权 + 限流 + 审计」门面，不重写业务接口。

---

## 二、现状

- Phase 5 P5.1 已实现：Agent / Workflow / Execution / Memory / Registry / Trace 六个 Controller + RouteDefinition + ServicePort。
- 已有 platform/api/（contracts、controllers、routes、service_ports）。
- 缺：API Key 鉴权、统一网关、速率限制、版本化、外部消费者管理。

---

## 三、开放平台能力

- API Key 鉴权（区别于用户登录态）
- 统一网关（入口 + 路由 + 限流 + 审计）
- 速率限制（per key / per tenant）
- 版本化（v1 契约稳定，路由带版本前缀）

---

## 四、鉴权模型

- API Key 代表「外部系统身份」，与 P10.1 的用户登录态（人身份）区分。
- 密钥只存哈希（key_hash），不落明文；签发后仅展示一次。
- scopes 限定可调用范围（如 agent.execute / memory.read）。
- OAuth 预留为后续扩展，不在本期实现。

---

## 五、网关与限流

    外部请求
      ↓
    网关鉴权（API Key + scope）
      ↓
    速率限制（复用 P10.2 计数）
      ↓
    路由到 Controller
      ↓
    审计（复用 P10.4）

---

## 六、数据模型

- api_key（id, tenant_id, key_hash, name, status, scopes, rate_limit, expires_at, created_time）
- api_consumer（id, tenant_id, name, contact, status）
- rate_limit_policy（consumer_id, resource_type, period, limit）

---

## 七、与现有 platform/ 集成

- 复用 platform/api/ 的 Controller / Route，前面加鉴权 + 限流中间件。
- 审计复用 P10.4，配额 / 速率复用 P10.2 的计数事实，避免两套计数口径冲突。
- 租户上下文复用 P10.1 的服务端注入。

---

## 八、验收标准

- 无 key / 无效 key / scope 不匹配均被拒。
- 速率超限被拒并返回 429。
- 每次 API 调用产生审计记录（复用 P10.4）。

---

## 九、风险

- 密钥只存哈希，任何日志 / 审计不得回显明文 key。
- 速率限制与配额口径对齐，避免双重扣减或漏计。
- 开放 API 扩大攻击面，必须以审计 + 限流兜底，不能只靠 key 保密。

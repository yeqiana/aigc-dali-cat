# Story OS V3 Phase10-P10.4 Audit & Compliance 详细设计 V1.0

更新时间：2026-09-11

项目：Story OS

分支：story-platform-v3

---

## 一、目标

把 Phase 6.6 的 audit_log 设计与 Phase 9 的 RuntimeAuditComplianceLayer 演进为「企业级审计日志」：持久化、多租户、append-only、可追溯。核心原则：审计只记录事实，不授权、不执行、不回滚。

---

## 二、现状

- Phase 6.6 已设计 audit_log（谁 / 何时 / 操作什么 / 结果如何）。
- Phase 9 已有 platform/operations/runtime_audit_compliance_layer.py（内存 AuditRecord，仅治理证据，不持久化、不授权）。
- 缺：持久化存储、多租户隔离、不可篡改、统一审计入口。

---

## 三、审计事件模型

统一字段：

- who：actor_type（USER / SERVICE / SYSTEM）+ actor_id
- when：created_time（UTC 统一）
- what：resource_type + resource_id
- action：操作码
- result：SUCCESS / FAILURE / DENIED
- 附加：tenant_id、request_id、ip、detail（敏感字段脱敏）

---

## 四、审计范围

- 登录 / 登出
- 资源 CRUD（project / workflow / agent / memory / artifact）
- Agent / Workflow 执行
- 权限变更（role / member）
- 配额变更（quota_policy）
- 计费事件（subscription / billing_record）
- Runtime 治理变更（复用 Phase 9 governance evidence）

---

## 五、数据模型

- audit_log（id, tenant_id, actor_type, actor_id, action, resource_type, resource_id, result, detail, request_id, ip, created_time）

约束：

- append-only：不提供 UPDATE / DELETE 业务接口，防篡改。
- tenant_id 由服务端注入（与 P10.1 一致），不接受客户端传入。
- detail 存 JSON，敏感字段（密钥、token、密码）写入前脱敏。

---

## 六、审计特性

- 不可篡改：append-only + 只读查询接口。
- 可追溯：request_id 串联一次请求的多条审计记录。
- 分级保留：普通事件按策略滚动归档，DENIED / 权限变更类高价值事件长期保留。

---

## 七、与现有 platform/ 集成

- 演进 platform/operations/runtime_audit_compliance_layer.py：内存记录抽象为统一 AuditSink，默认落 MySQL，测试可替换为内存实现。
- 新增 platform/audit/（sink、record、query、mask）。
- 与 platform/tenant/（P10.1）绑定 tenant_id；与 platform/quota/、platform/billing/ 的变更点埋审计。

---

## 八、验收标准

- 审计记录持久化且不可经业务接口篡改。
- DENIED（越权拒绝）事件被审计，跨租户访问被记录。
- 敏感字段脱敏（无明文密钥 / token 落库）。

---

## 九、风险

- 审计写入失败不阻断业务主流程（异步落盘 + 失败告警）。
- 审计日志体积增长需归档策略，避免无限膨胀。
- 脱敏规则须覆盖所有凭据字段，避免合规泄漏。

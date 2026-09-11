# Story OS V3 Phase 10 Enterprise Runtime Platform 启动前评估与方案设计 V1.0

更新时间：2026-09-11

项目：Story OS

分支：story-platform-v3

---

## 一、目标

Phase 10 把 V3 从「单实例平台化」演进为「多租户企业级运行时平台（Enterprise Runtime Platform）」。它不是从零重造，而是把 Phase 6 的 SaaS Ready / Plugin Extension 设计、Phase 7 的前端多租户与市场 foundation 从「预留」落地为「真实能力」。

方向（此前已定）：多租户 / 权限、计费 / 计量、插件市场 / Agent 市场、Runtime Federation、外部 API / Open Platform、SaaS 部署。

---

## 二、启动条件复核（2026-09-11）

| 条件 | 状态 |
| --- | --- |
| Phase 8 生产切换闭环 | ❌ 待 #7 授权（switch --apply） |
| Phase 9 Runtime Operations 验证 | ✅ 代码侧全量回归 515 + 16 全绿 |
| platform tests 全绿 | ✅ 329 + 186(+16) |

结论：Phase 10 正式实施以 #7 生产归属切换闭环为硬前提；启动前评估与方案设计可先行，不写任何生产代码。

---

## 三、现状盘点（Phase 6 / Phase 7 已有 foundation）

| 能力 | 已有基础 | 缺口 |
| --- | --- | --- |
| 多租户 | Phase 6.6 tenant / tenant_member 设计；Phase 7.5.11 前端 TenantContext / UserContext / PermissionGuard | 后端真实租户隔离与 RBAC 未落地 |
| 权限 | Phase 6.2 Identity Permission 设计 | 真实认证 / 授权链未落地 |
| 配额 | Phase 6.6 quota_policy / quota_usage 设计 | 计量执行未落地 |
| 计费 | Phase 6.6 subscription / plan / billing_record 预留 | 计费基础未落地（不实现支付） |
| 审计 | Phase 6.6 audit_log 设计；platform/operations 有 audit 模块 | 企业级审计闭环未落地 |
| 插件 | Phase 6.5 Plugin Extension 设计 | 运行时加载 / 生命周期未落地 |
| 市场 | Phase 7.5.14 Agent / Skill Marketplace（前端） | 后端 catalog / 分发未落地 |
| 平台 API | Phase 5 P5.1 Platform API Layer | 开放平台鉴权 / 网关未做 |
| 部署 | Phase 7.5.15 Console Release / Deployment foundation | 多租户部署形态未做 |

---

## 四、Phase 10 分阶段任务拆解（草案）

- P10.1 Enterprise Tenant & RBAC：后端 tenant 隔离 + 真实 RBAC，把 TenantContext 从前端下沉到服务端强制。
- P10.2 Quota & Metering：quota_policy / quota_usage 落地，运行时计量（图片生成、Agent 执行、Token、存储）。
- P10.3 Billing Foundation：subscription / plan / billing_record 落地，与支付解耦，仅记账预留。
- P10.4 Audit & Compliance：audit_log 落地，覆盖谁 / 何时 / 操作什么 / 结果如何。
- P10.5 Runtime Federation：多运行时（WORK / CODEX / WEB）联邦编排，统一调度与失败转移。
- P10.6 Open Platform / External API：外部 API + API Key / 网关 / 速率限制。
- P10.7 Plugin & Agent Marketplace：后端 catalog、分发、版本与安全审核。
- P10.8 SaaS Deployment：多租户部署形态（单实例多租户 vs 实例隔离）与配置治理。

---

## 五、技术架构蓝图（基于现有 platform/ 结构演进）

    Tenant
      ├─ User (RBAC)
      ├─ Project
      ├─ Quota / Billing / Audit
      ├─ Agent / Workflow / Memory / Artifact
      ├─ Runtime Federation
      ├─ Open Platform API
      └─ Plugin / Agent Marketplace

新增 / 强化的 platform 子域方向：

- platform/tenant/（tenant、member、rbac 强制层）
- platform/quota/（policy、usage、metering）
- platform/billing/（subscription、plan、billing_record）
- platform/federation/（runtime 联邦编排）
- platform/openapi/（外部 API、api key、网关）
- platform/marketplace/（catalog、分发、审核）

---

## 六、风险与依赖

- #7 生产归属切换是硬前提；未闭环前不启动 Phase 10 实施。
- 多租户隔离是安全边界，须服务端强制（不能只靠前端 PermissionGuard）。
- 计费 / 支付属合规敏感，Phase 10 只做记账预留，与支付解耦。
- Runtime Federation 涉及跨运行时调度，须先复用 Phase 8/9 的 Canary / Recovery 证据链。

---

## 七、结论

Phase 10 启动前评估完成：能力缺口已盘点，分阶段任务已拆解为 P10.1–P10.8，架构演进方向已明确。正式实施待 Phase 8 #7 生产归属切换授权闭环后启动，当前不写生产代码。

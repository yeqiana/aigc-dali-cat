# Story OS V3 Phase10-P10.1 Enterprise Tenant & RBAC 详细设计 V1.0

更新时间：2026-09-11

项目：Story OS

分支：story-platform-v3

---

## 一、目标

把 Phase 6.2 Identity & Permission 与 Phase 6.6 SaaS Ready 的设计从「预留」落地为后端真实实现：服务端强制租户隔离 + RBAC。核心原则是「权限控制资源访问，不控制业务流程」「前端 TenantContext 只做展示，服务端才做强制」。

---

## 二、现状

- Phase 6.2 已设计：user_identity / role_definition / permission_definition / user_role_relation / role_permission_relation / project_member。
- Phase 6.6 已设计：tenant / tenant_member（OWNER / ADMIN / MEMBER / VIEWER）。
- Phase 7.5.11 已实现：前端 TenantContext / UserContext / PermissionGuard（仅前端，可被伪造，不作为隔离依据）。
- platform/ 后端当前无 tenant / permission 模块，RBAC 未落地。

---

## 三、数据模型（合并 Phase 6.2 + 6.6）

核心表：

- tenant（id, tenant_code, name, status, created_time, updated_time）
- tenant_member（id, tenant_id, user_id, role_id, status, created_time, updated_time）
- user_identity（id, username, email, password_hash, status, created_time, updated_time）
- role_definition（id, role_code, role_name, status）
- permission_definition（id, permission_code, permission_name, resource_type, action）
- role_permission_relation（id, role_id, permission_id）
- project_member（id, project_id, user_id, role_id, status）

关键约束：

- 所有核心资源（project / workflow / agent / memory / artifact / execution）加 tenant_id 列。
- tenant_member 同时绑定 tenant 与 role，形成「User → Tenant(role) → Project(role) → Resource」链路。
- tenant_id 由服务端注入，不接受客户端传入，防跨租户越权。

---

## 四、租户隔离强制策略（三层）

1. API 层：鉴权中间件解析登录态，得到 tenant_id + user_id + role，写入服务端请求上下文。
2. Repository 层：所有租户化资源查询强制带 tenant_id 过滤，杜绝「忘记过滤」导致的越权。
3. 存储层：核心表物理加 tenant_id 列，隔离可下推到 SQL 索引。

禁止：以前端 TenantContext / PermissionGuard 作为唯一隔离依据。

---

## 五、RBAC 模型

    User
      ↓
    tenant_member（角色）
      ↓
    role_definition
      ↓
    permission_definition（resource_type + action）
      ↓
    Resource

默认角色：TENANT_OWNER / ADMIN / MEMBER / VIEWER。

权限示例：agent.read / agent.execute / workflow.run / memory.read / mcp.invoke / image_generation / system_config。

判定规则：permission_code = resource_type + action；RBAC 引擎只做「是否授权」，不插入业务流程。

---

## 六、AI Agent 权限链

    User Request
      ↓
    Permission Check（用户身份）
      ↓
    Agent Orchestrator
      ↓
    Skill Permission（服务身份）
      ↓
    MCP Permission（服务身份）
      ↓
    Runtime Execute

约束：

- Agent 服务身份（service identity）与用户身份分离；Agent 调用 Skill / MCP 需显式授权。
- Agent 不得自行绕过权限校验；image_generation / memory_admin / system_config 等敏感权限单独收敛。

---

## 七、落地路径（分步，不破坏现有生产）

1. 建 tenant / tenant_member / user_identity / role / permission 表 + 基础 CRUD。
2. 实现 RBAC 判定引擎（platform/tenant/rbac.py），纯函数，离线可测。
3. 实现 API 鉴权中间件（platform/api/auth_middleware.py），解析登录态注入上下文。
4. Repository 层加 tenant 过滤（对现有 repository 逐项小步改造）。
5. 数据迁移：现有单租户数据归入默认 tenant（default_tenant），保证不回归。

---

## 八、与现有 platform/ 集成点

- platform/tenant/（新增：tenant、member、rbac、context）
- platform/api/（新增鉴权中间件）
- platform/repository/（加 tenant 过滤）
- platform/validation/（复用权限校验结果，不另起一套）

---

## 九、验收标准

- 跨租户访问被服务端拒绝（而非仅前端隐藏）。
- RBAC 判定引擎有角色 × 权限矩阵的离线单测覆盖。
- 现有单租户行为不回归（tests/platform + tests/system 保持全绿）。

---

## 十、风险

- 租户隔离是安全边界，必须服务端强制 + 测试覆盖，不接受「前端已隐藏」作为通过理由。
- 核心表加 tenant_id 的迁移须分步，避免大表锁表。
- 与 Runtime 执行模型解耦，不改变 Agent 执行语义。

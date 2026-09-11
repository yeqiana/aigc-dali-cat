# Story OS V3 Phase10-P10.8 SaaS Deployment 详细设计 V1.0

更新时间：2026-09-11

项目：Story OS

分支：story-platform-v3

---

## 一、目标

把 Phase 6.6 SaaS Ready 预留的「多租户 SaaS」与 Phase 7.5.15 的部署 foundation，落地为可选的部署形态与配置治理方案。核心原则：单实例多租户为默认，实例隔离为合规升级路径，混合形态按租户分级切换，不强制一套到底。

---

## 二、现状

- Phase 6.6 已定义 tenant / tenant_member / quota_policy / quota_usage / subscription / audit_log 预留模型，但租户隔离未在服务端强制。
- Phase 7.5.15 已有 Web Console → Docker Build → Nginx → Platform API 的部署链路，缺 CI/CD、K8s、Environment Profile、Health Check、Release Version Management。
- 缺：多租户部署形态选型、租户级配置覆盖、实例隔离切换与数据隔离治理。

---

## 三、部署形态选型

    单实例多租户（Shared，默认）
      ├─ 共享 DB / Redis / Runtime Worker
      ├─ 靠 tenant_id 列级强制隔离
      ├─ 成本低，适合中小租户
      └─ 隔离强度中

    实例隔离（Dedicated）
      ├─ 每租户独立 DB schema / 实例 / Runtime Worker
      ├─ 物理级隔离，适合合规 / 企业租户
      ├─ 成本高
      └─ 隔离强度高

    混合（Hybrid，推荐）
      ├─ 默认 Shared
      ├─ 高合规 / 大租户按需升 Dedicated
      └─ 反向代理按 tenant 路由到 shared 池或 dedicated 实例

---

## 四、配置治理

- 环境 Profile：dev / staging / prod 分层，复用 P6.4 Config Center 与 Phase 7 前端环境变量入口，实例启动时注入当前 profile。
- 密钥注入：DB / Redis / API Key 等敏感配置走外部注入（env / secret），不进仓库、不进镜像层（复用 P10.6 只存哈希原则）。
- 租户级覆盖：共享实例内按 tenant 覆盖限流 / 配额 / 审计保留策略，避免为单租户改动实例级配置。
- 配置优先级：实例默认 < 环境 profile < 租户覆盖 < 显式运行参数，冲突时取高优先级并留审计记录。

---

## 五、数据与资源隔离

- Shared：MySQL 行级 tenant_id 强制过滤，服务端注入（复用 P10.1），不得只靠前端。
- Dedicated：独立 DB schema / 独立 Runtime Worker，物理隔离。
- Redis：Shared 用 tenant 前缀 key；Dedicated 用独立 DB index 或独立实例。
- Runtime Worker：Shared 共享 worker 池但按 tenant 调度与计数（复用 P10.2）；Dedicated 独立 worker，避免噪音邻居。

---

## 六、部署链路演进

    现有（P7.5.15）
      Web Console → Docker Build → Nginx → Platform API

    Phase 10 补齐
      CI/CD
      Environment Profile
      Health Check（复用 Phase 9 health / alert 证据链）
      Release Version Management
      K8s Deployment（可选，多租户路由）

多租户路由：

    入口反向代理
      ↓
    按 tenant_id 解析
      ↓
    shared 池 / dedicated 实例

---

## 七、与现有 platform/ 集成

- 租户隔离复用 P10.1，计量 / 配额复用 P10.2，审计复用 P10.4，外部接入复用 P10.6。
- 部署健康与告警复用 Phase 9 的 health / alert / recovery 组件，不另起一套监控口径。
- 新增 platform/deployment/（profile、release version、health 探针）作为 Phase 10 子域。

---

## 八、验收标准

- 共享实例下跨租户访问被服务端拒绝，前端隐藏不可作为隔离依据。
- 租户可从 Shared 升 Dedicated，升级过程幂等且数据不串租。
- 敏感密钥不出现在镜像 / 日志 / 仓库；配置覆盖变更留审计。
- 部署链含 Health Check 与 Release Version，可区分当前运行版本并回滚。

---

## 九、风险

- 列级 tenant_id 隔离若只落在应用层，任何漏写都会造成跨租户泄露，须在数据访问层统一强制。
- Dedicated 升级涉及数据搬迁与运行时切换，须幂等、可回滚，不能中途串写。
- 配置覆盖若口径不统一，易出现多实例间漂移，须以单一配置事实源收敛。
- K8s / CI/CD 属可选增强，不得为求形态完整而提前引入，保持最小可交付。

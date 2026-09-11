# Story OS V3 Phase10-P10.7 Plugin / Agent Marketplace 详细设计 V1.0

更新时间：2026-09-11

项目：Story OS

分支：story-platform-v3

---

## 一、目标

把 Phase 6.5 的 Plugin Extension 数据模型与 Phase 7.5.14 的前端 Marketplace 入口，落地为后端的「目录 + 发布 + 分发 + 版本 + 安全审核」能力，形成可扩展的 Agent / Skill / MCP / Plugin 生态。

核心原则：复用 Phase 6.5 已定模型，不重造；市场只做编目与分发，插件运行时能力仍由既有 Plugin Manager / Agent Runtime 承担。

---

## 二、现状

- Phase 6.5 已有数据模型设计：plugin_definition / plugin_version / plugin_capability / plugin_permission，生命周期 Install → Enable → Running → Disable → Uninstall，但未实现运行时加载与生命周期。
- Phase 7.5.14 已有前端：web-console/src 的 api/marketplace.ts、types/marketplace.ts、pages/MarketplaceConsole.tsx，仅展示层，后端 catalog 为空。
- Phase 3 P3.2 Skill Registry、P3.3 MCP Registry 已有编目基础；运行时经 skill_runtime_adapter / mcp_tool_adapter 接入。
- 缺：后端 catalog、发布 / 审核流、分发 / 安装、版本灰度与回滚、能力评分、第三方插件安全审核。

---

## 三、市场能力

    用户 / 开发者
        │
        ├─ 浏览 Catalog（agent / skill / mcp / plugin 统一编目）
        ├─ 发布（提交 → 审核 → 上架）
        ├─ 安装（租户内启用，多租户隔离）
        ├─ 版本（语义化版本 + 灰度 + 回滚）
        └─ 信任（能力评分 / 下载量，后续扩展）

---

## 四、目录与分发模型

Catalog 是统一编目索引，不复制 Agent / Skill / MCP 的权威定义，只聚合来源引用：

- 官方内置：随平台发布，默认可见、默认可用，走 version 生命周期。
- 第三方发布：开发者提交，经审核上架，租户按需安装。
- 私有资产：租户 / 项目私有，不进公开目录，只对归属方可见。

分发链路：

    目录浏览
      ↓
    安装（写 tenant 安装态，绑定版本）
      ↓
    启用（写入 Plugin Manager 可解析清单）
      ↓
    运行（复用 Plugin Manager → Platform API → Execution Record）

---

## 五、发布与安全审核

发布状态机（plugin_version.release_status）：

    DRAFT → SUBMITTED → REVIEWING → APPROVED → PUBLISHED → DEPRECATED
                              ↓
                          REJECTED

审核双层：

- 自动化门禁：清单完整性、依赖声明、权限声明、代码静态扫描、可复现包校验。
- 人工复核：第三方插件必须人工确认权限最小化、无越权、无明文密钥。

安全边界：

- 插件权限以 plugin_permission 为准，默认拒绝，白名单授权。
- 插件执行必须进 Trace / Event / Artifact，不得绕过审计（复用 P10.4）。
- API Key / 敏感配置只存哈希或由平台注入，插件包内不得落明文（复用 P10.6）。

---

## 六、数据模型（演进 Phase 6.5）

- plugin_definition：新增 owner（官方 / 第三方）、visibility（public / private）、tenant_id（私有归属）、marketplace_status。
- plugin_version：release_status 按上节状态机；package_info 增加 manifest、checksum、dependencies、permissions 声明。
- plugin_capability：能力枚举（image_generation / video_generation / custom_review 等），供 Agent Orchestrator 能力发现。
- plugin_permission：白名单授权，与 P10.1 RBAC 对齐。
- 新增 plugin_review（审核记录：submit / approve / reject 时间线，复用 P10.4 审计）。
- 新增 plugin_install（tenant 安装态：tenant_id + plugin_id + version + enabled）。
- 可选 plugin_rating（评分 / 下载量，后续扩展，本期仅预留）。

---

## 七、与现有 platform/ 集成

- 复用 platform/api/ 的 Controller / Route / ServicePort，新增 MarketplaceServicePort 与 CatalogController，不改既有六 Controller 契约。
- Agent / Skill / MCP 编目引用现有 Registry，运行时仍走 skill_runtime_adapter / mcp_tool_adapter / agent_runtime，市场不重建执行链。
- 租户上下文复用 P10.1 服务端注入；安装 / 调用配额复用 P10.2 计数；审核与操作审计复用 P10.4；对外分发密钥复用 P10.6。
- 新增 platform/marketplace/（catalog、publish、distribution、review）作为 Phase 10 子域。

---

## 八、验收标准

- 目录可枚举官方与已上架第三方资产，私有资产不泄露给其他租户。
- 第三方插件未经 APPROVED 不可被安装；REJECTED 不可上架。
- 安装与启用写入 tenant 安装态与版本绑定，禁用后不可再调用。
- 插件调用产生 Trace / Event / Audit 记录，权限拒绝默认生效。
- 版本支持灰度发布与回滚，回滚到前一已发布版本可复现。

---

## 九、风险

- 第三方插件是主要攻击面，必须默认拒绝 + 最小权限 + 沙箱执行，不能只靠目录审核。
- 目录聚合不得破坏 Agent / Skill / MCP 的权威定义，避免双写产生口径漂移。
- 分发与安装涉及跨租户隔离，须服务端强制，不能只靠前端隐藏。
- 评分 / 信任机制涉及刷量风险，本期只预留，不仓促上线。

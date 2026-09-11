# Story OS V3 Phase10-P10.5 Runtime Federation 详细设计 V1.0

更新时间：2026-09-11

项目：Story OS

分支：story-platform-v3

---

## 一、目标

把 V2.0 Multi-Runtime（WORK / CODEX / WEB 创作运行时）与 Phase 9 本机平台运维运行时，统一为 Runtime Federation：统一调度、能力匹配、失败转移。核心原则：联邦层只做「调度与转移」，不改变各运行时的执行语义，也不建立第二状态机。

---

## 二、现状

- V2.0 Multi-Runtime：runtimes/CODEX.md / WORK.md / WEB.md，自动路由（可写文件系统 + terminal → CODEX，否则 WORK，否则 WEB）。
- Phase 9：本机平台运行时（Worker + Metrics + Recovery + Canary），已有健康、恢复、流量路由能力。
- 缺：运行时作为「可注册、可监控、可转移的节点」的统一联邦编排；跨运行时失败转移。

---

## 三、联邦模型

- runtime_node：运行时节点，注册 + 健康心跳 + 能力声明。
- capability：能力维度（image_generation / code_execution / file_system / long_task / web_only）。
- 路由策略：任务能力需求 → 候选运行时排序 → 健康过滤 → 选择。

---

## 四、调度流程

    任务
      ↓
    能力解析（需要什么）
      ↓
    候选运行时排序（偏好 + 成本 + 可用性）
      ↓
    健康检查（复用 Phase 9 探针）
      ↓
    分发执行
      ↓
    失败转移（降级到 fallback）
      ↓
    结果回执

---

## 五、数据模型

- runtime_node（id, runtime_type, status, health, last_seen, capability_list）
- runtime_capability（runtime_id, capability, cost_weight, availability）
- federation_route（task_type, preferred_runtime, fallback_order, created_time）

---

## 六、失败转移

- 运行时不可用 / 健康降级时，按 fallback_order 降级到备用运行时。
- 复用 Phase 9 Recovery 的自愈信号（runtime_unhealthy → 触发转移）。
- 转移必须幂等：同一任务不因重试重复执行（task_id + 执行回执去重）。

---

## 七、与现有 platform/ 集成

- platform/federation/（新增：node、capability、route、scheduler）
- 复用 Phase 8 Canary 的流量路由能力、Phase 9 Recovery / Worker 的健康与转移信号。
- 与平台运维运行时（Worker + Metrics）共用健康事实，不另起一套探针。

---

## 八、验收标准

- 能力匹配正确（例如 image_generation 只路由到具备该能力的运行时）。
- 运行时不可用时正确降级，且任务不重复执行。
- 现有 V2.0 创作运行时路由不回归（CODEX / WORK / WEB 自动选择保持原行为）。

---

## 九、风险

- 跨运行时状态一致性：任务执行结果须回执去重，避免重放。
- 失败转移须幂等，不能因转移导致重复出图 / 重复扣配额。
- 联邦层不得成为第二状态机，最终阶段事实源仍是各运行时的既有权威。

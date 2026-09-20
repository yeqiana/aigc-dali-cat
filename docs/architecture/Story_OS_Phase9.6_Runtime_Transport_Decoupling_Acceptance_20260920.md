# Story OS Phase9.6 Runtime Transport / Provider Decoupling 验收报告

- 日期：2026-09-20
- 分支：story-platform-v3
- 状态：ACCEPTED / FROZEN
- 范围：Runtime Workspace Transport / Provider 解耦、DevSpace → WebCodex、PUBLISH_READY 终态一致性
- 非范围：web-console UI 改造（并行工作流，未纳入本报告）

## 1. 结论

Phase9.6 已完成并通过验收。

Story OS 的业务 Runtime 与 Workspace 工具已正式拆层：

- 创作/治理 Runtime：WORK
- 图片执行：CODEX_IMAGE
- 像素视觉审核：CODEX_VISION
- 本地确定性动作：MACHINE
- 外部动作：EXTERNAL
- Workspace Provider：webcodex
- Workspace Transport：WEBCODEX
- Provider Execution Mode：host_mcp_runner

WebCodex 只负责给 WORK 提供本地 Project/Workspace 访问能力，不是 Episode Runtime，不拥有 Episode Authority，也不会被 Story OS 当成本地 CLI/subprocess 启动。

## 2. DevSpace 替换结果

### 2.1 已移除的生产绑定

以下旧生产绑定已移除：

- config/storyos.yaml 中 review.text / review.governance / legacy review 的 DEVSPACE 硬编码
- runtime.review.allow_webcodex=false 旧反向开关
- runtime.review.bounded_devspace_provider 悬空 fallback 设计
- work_host_action_executor.py 本地 DevSpace agent/subprocess 执行旁路
- review_status_probe DevSpace polling timeout
- Product Runtime / Product Review 请求中的 devspace_bounded_fallback_allowed
- 新请求对 WORK_DEVSPACE_BOUNDED 的生成能力

### 2.2 保留的 DevSpace 内容

runtime_provenance.py 保留 LEGACY_DEVSPACE_* 只用于历史证据读取/恢复兼容。

该兼容层：

- 不参与新生产路由
- 不生成新的 DevSpace bounded request
- 不作为 Workspace Provider
- 不作为 action executor
- 不作为 Episode Authority

## 3. Workspace Provider Registry

新增：

- episodes/_system/workspace_provider.py

Canonical 配置：

```yaml
runtime:
  workspace:
    provider: webcodex
    transport: WEBCODEX
    execution_mode: host_mcp_runner
```

Provider 契约明确：

- host_managed=true
- local_subprocess=false
- WebCodex 通过外层 WORK / MCP / Runner 访问已注册 Project
- Story OS 不假造 webcodex.exe，也不直接 spawn WebCodex

## 4. Runtime Executor Contract

新增：

- episodes/_system/runtime_executor_role.py

新生产 action executor 只允许：

```text
WORK
CODEX_IMAGE
CODEX_VISION
MACHINE
EXTERNAL
```

以下标签禁止成为新 action executor：

```text
DEVSPACE
WEBCODEX
WEB
CODEX
WORK_ISOLATED
```

说明：

- WEBCODEX 是 transport/provider，不是 Runtime
- WORK_ISOLATED 等仍可作为 critic provenance 历史/审计语义，不作为业务 action executor

## 5. Product Runtime / Review 契约

Product Runtime Host Request 与 Product Review Request 统一从 Workspace Provider Registry 获取 Provider 契约。

新 Product Review 请求升级为 schema_version=4，并记录：

- workspace_provider=webcodex
- workspace_transport=WEBCODEX
- workspace_execution_mode=host_mcp_runner
- workspace_host_managed=true
- webcodex_allowed=true

文本/治理审核仍属于 WORK；WebCodex 只提供 Workspace Access。

## 6. PUBLISH_READY 状态漂移修复

真实 Episode 抽样发现，部分已进入 MySQL Authority=PUBLISH_READY 的 Episode 仍可能被旧 Production Ledger / Queue 残留重新路由到：

- USER_DECISION_REQUIRED
- REVIEW_FINAL_PRODUCTION

根因：

next_action 在判断 canonical production success 前，先处理了旧队列/旧审核残留。

修复后：

- PUBLISH_READY / PUBLISHED / DATA_REVIEWED 的 canonical success 优先于普通历史 residue
- 普通 REPAIR_READY / NEEDS_USER / 未完成旧 review 不再重开生产
- 只有明确带 user-continuation-* 或 user-exception-* capture id 的用户授权候选可以在终态后继续进入对应视觉审核

这与 runtime_resume_capsule 的原则一致：

> complete; do not reopen production unless user requests changes

## 7. 真实 Episode 验收

扫描 MySQL Authority=PUBLISH_READY 的真实 Episode：

1. 09_旧物怪谈/04_瓶中世界
2. 09_旧物怪谈/05_婚礼前夜_记忆麻醉
3. 10_山难伪纪录片/01_鳌太线_热汤
4. 11_仲夏夜惊魂/01_停电夜蜕壳

修复后四个 Episode 均返回：

```text
action=COMPLETE
executor=WORK
work_pending=false
hard_stop=false
```

其中《婚礼前夜_记忆麻醉》的 MySQL stage history 已确认完整：

```text
IDEA_LOCKED
→ STORYBOARD_LOCKED
→ VISUAL_CALIBRATED
→ PRODUCTION_PASSED
→ PUBLISH_READY
```

## 8. 回归结果

### Provider / Golden Path 定向回归

```text
116 passed
```

### Canonical Full Auto Integration

```text
24 passed
```

### tests/platform

```text
446 passed
5 warnings
```

warnings 为既有 datetime.utcnow deprecation，不是 Phase9.6 回归。

### tests/system

最终：

```text
1248 passed
1 skipped
90 subtests passed
```

### Config / Compile / Diff

```text
storyos_config.py validate: PASS
Phase9.6 changed Python modules py_compile: PASS
git diff --check: PASS
```

## 9. Authority 边界

Phase9.6 没有改变 Phase9.5 已冻结的 Authority：

- Episode durable authority：MySQL
- hot/runtime state：Redis
- content artifacts / exports：File/Object boundary
- Workspace Provider：不拥有 Authority

WebCodex 不写入第二套 Episode 状态机，也不成为新的 Authority。

## 10. 最终状态

Phase9.6 Runtime Transport / Provider Decoupling：

- DevSpace production dependency：REMOVED
- WebCodex Workspace Provider：ACTIVE
- Runtime / Provider layering：PASS
- bounded_devspace_provider dangling config：REMOVED
- Local DevSpace execution bypass：REMOVED
- PUBLISH_READY stale residue reopening：FIXED
- Real Episode validation：PASS
- Platform tests：PASS
- System tests：PASS

**Phase9.6 ACCEPTED / FROZEN。**

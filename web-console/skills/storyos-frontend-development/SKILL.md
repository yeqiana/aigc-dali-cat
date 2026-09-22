---
name: storyos-frontend-development
description: StoryOS 专用的前端开发、界面审查、React 性能优化及生产监控台工程落地技能 (V1.0 冻结版)。整合 Impeccable (Operate 模式与视觉闭环)、Vercel React Best Practices (并发与高频渲染优化)、Web Design Guidelines (无障碍与可用性)、Jakub Better Interface (精细排版与视觉 Token) 以及 Microsoft Frontend Design Review (验收门禁)。
---

# StoryOS Frontend Development Skill (V1.0)

## 1. Instruction Priority (规则冲突优先级)

当多个规则、Skill、项目规范发生冲突时，按以下优先级执行：

1. **用户当前任务中的明确要求**
2. **仓库级 AGENTS.md / CONTRIBUTING.md / 强制工程约束**
3. **StoryOS 已冻结的业务 Contract**
4. **StoryOS Design System / Theme / Token / API Schema**
5. **storyos-frontend-development Skill**
6. **当前模块已经采用的稳定实现模式**
7. **外部 Skill / Best Practice / Reference**
8. **Agent 自身偏好**

> 高优先级规则覆盖低优先级规则。

外部 Skill 永远不能覆盖：
- StoryOS 已有 Design Token；
- StoryOS Status Contract；
- API Contract；
- 已冻结的业务语义；
- 当前仓库明确工程规范。

*示例*：如果外部 Skill 推荐 `border-radius: 16px`，而 StoryOS Token 为 `--radius-panel: 6px` 或既定规范，必须使用 StoryOS Token。不得为了符合外部 Best Practice 擅自改变项目已冻结约束。

---

## 2. Source of Truth (唯一事实源)

Skill 定义使用规则，不重复维护业务事实。

以下内容以项目代码 / Contract 为最终 Source of Truth：
- Status Enum (`/src/types.ts`)
- Stage Enum (`/src/types.ts`)
- Runtime Action
- API Schema
- Permission
- Design Token (`/src/index.css`)
- Route
- Feature Flag
- Runtime Config

Skill 可以规定：
- `RUNNING` 应使用 success/running semantic；
- `RETRYING` 必须展示 attempt 进度。

但不得规定：
- `RUNNING = #22C55E`（具体颜色必须来自当前 Theme / Token）；
- 重试最大次数硬编码为固定 3 次（必须读取实际后端 Contract）。

如果 Skill 描述与代码 Contract 不一致：
**以当前已确认的 Contract 为准**，同时将 Skill 漂移记录为待治理问题，不得同时维护两套事实。

---

## 3. Preflight (动代码前先锁范围)

在正式修改代码前，必须形成简短 Preflight：

```text
Task Type:
BUGFIX / CREATE / EXTEND / REVIEW / POLISH / PERFORMANCE / ACCESSIBILITY / REFACTOR

Target:
本次修改目标。

Scope:
涉及模块 / 页面。

Expected Files:
预计修改文件范围（通常 ≤ 3 个）。

Existing Components:
预计复用的公共组件与设计令牌。

Contract Impact:
NONE / READ_ONLY / CHANGE_REQUIRED

Risk:
LOW / MEDIUM / HIGH

Verification:
计划执行的验证方式。
```

### 范围漂移检测
如果实际修改明显超过 Preflight（如预计修改 2 个文件实际改动 15 个，或原定 Contract Impact 为 NONE 实际需要改动 API Schema），**必须立即暂停并重新评估任务，不得静默扩大范围**。

---

## 4. Autonomous Change Boundary (自主修改边界)

### Agent 可以在当前任务内自主处理：
- 明显样式错误
- 局部布局问题
- TypeScript 类型错误
- 空状态 (Empty) 与加载状态 (Loading)
- 错误界面 (Error UI)
- 小范围 Accessibility (如缺失 aria 标注)
- 现有组件错误使用修补
- 明显重复请求与串行瀑布流
- 局部 rerender 性能问题
- 与当前需求直接相关的单元/契约测试补齐
- 当前修改导致的 lint / typecheck 问题

### Agent 不得在普通任务中自主执行：
- 修改 API Contract
- 修改业务状态模型
- 修改 StoryOS Stage 定义
- 修改权限模型
- 修改全局路由架构
- 更换 State Management
- 更换 UI Framework
- 大版本依赖升级
- 全局 Design System 重构
- 删除未知兼容逻辑
- 大范围目录迁移
- 改变 Runtime Action 业务语义
- 删除用户已有功能

若需求必须涉及上述变更，必须标记为 **SCOPE_ESCALATION**，说明原因和影响，不得伪装成普通任务扩大修改。

---

## 5. Git Safety (工作区安全规则)

修改代码前必须检查工作区状态（branch、tracked/untracked files、staged changes），默认认为未知改动属于用户或其他任务。

### 严禁执行：
- `git reset --hard`
- `git checkout -- .`
- `git restore .`
- `git clean -fd`
（除非用户明确要求并确认影响）

### 不得：
- 覆盖已有用户改动；
- 删除来源不明的文件；
- 为获得 clean tree 而回退其他修改；
- 自动格式化大量无关文件。

### 修改完成后确认：
检查 `git diff` 与 `git status`，确认只有预期文件变更，没有运行产物、敏感信息、临时截图或日志被提交。仅在用户明确要求时按 `feat`/`fix`/`test`/`docs`/`refactor` 规范拆分 Commit。

---

## 6. Rollback and Recovery (失败后的恢复规则)

如果本轮修改导致新的失败：
1. **第一优先级**：修复本轮修改本身（Targeted Fix）；
2. **第二优先级**：缩小本轮变更范围；
3. **第三优先级**：只撤销 Agent 在本轮明确产生的修改。

严禁全仓 reset、覆盖用户已有修改、删除未知代码，或者通过关闭测试、删除 assertion、吞掉 exception、掩盖 TypeScript 错误来规避失败。

如果无法确定修改归属，输出规范报告：
```text
BLOCKER: 失败原因
CHANGES_KEPT: 已确认安全的修改
CHANGES_REVERTED: 本轮已安全撤销的修改
USER_CHANGES_UNTOUCHED: 确认未触碰的原有修改
```

---

## 7. Verification Ladder (测试逐级扩大)

验证从最窄范围开始，根据风险逐级扩大：
- **Level 1 (Targeted)**: 单个 component/unit test、单文件 typecheck、对应 lint；
- **Level 2 (Module)**: 当前模块集成、相关 hooks 与页面交互验证；
- **Level 3 (Cross Module)**: 涉及共享组件、全局状态、路由或 Token 变更时的跨模块测试；
- **Level 4 (Full Regression)**: 核心公共资产或发布门禁时的全量回归。

| Task 类型 | 默认验证阶梯 |
| :--- | :--- |
| **BUGFIX** | Targeted → Module |
| **EXTEND** | Targeted → Module → 必要时 Integration |
| **CREATE** | Module → Browser → Integration |
| **POLISH** | Browser → 视口走查 |
| **PERFORMANCE** | Profiling → Targeted → Browser |
| **REFACTOR** | Module → Cross Module → Regression |
| **Release** | Full applicable regression |

---

## 8. Evidence-Based Browser QA (浏览器验收证据化)

需要浏览器验收的任务，不得仅口头声明“页面正常”，必须明确记录实际验证证据：

- **目标桌面视口**：`1366×768`、`1440×900`、`1536×864`、`1920×1080`；
- **关键状态验证**：`RUNNING`、`WAITING`、`RETRYING`、`BLOCKED`、`FAILED`、`COMPLETED`；
- **关键极限边界**：极长剧集名、极长 Run ID、Queue=0 与 999、Worker=0/4 与 4/4、Heartbeat 3s 与 180s、Frame 0/20 与 20/20、异常数量=0 与异常堆叠；
- **关键交互保持**：Filter/Search/Sort 触发无误，自动刷新期间 Frame Drawer 保持展开，用户滚动位置、Tab 与输入状态不丢失；
- **控制台与网络**：0 运行时报错，0 异常失败请求。

---

## 9. External Skill Governance (外部 Skill 治理)

StoryOS 不直接依赖外部 Skill 的动态拉取与最新行为变更。
外部 Skill 仅作为 **REFERENCE KNOWLEDGE**（见 `references/external-skills.md`），StoryOS 本地 Skill 才是唯一的 **STABLE PROJECT CONTRACT**。
禁止每次运行任务时自动拉取 GitHub 最新外部 Skill 并随意改变 Agent 的交互规范。

---

## 10. StoryOS UI & 架构核心原则

- **Operate 运维模式优先**：这是生产监控中枢，不是营销展示页。扫描效率 > 视觉装饰；
- **一屏回答四个核心问题**：谁在运行？跑到哪里？谁有异常？是否需要人工处理？
- **渐进式披露 (Progressive Disclosure)**：总控视图保持紧凑，深层排障与技术参数下沉至右侧 Drawer；
- **状态文字强绑定**：严禁单靠颜色区分状态；
- **合法动作控制**：`PASSED` 状态绝不允许出现“跳过”操作；高危破坏性操作配有二次确认模态。

---

## 11. StoryOS Frontend Skill V1 Freeze Contract

本 Skill 旨在稳定、可预测、最小风险地交付 StoryOS 前端工程任务。

### 默认执行顺序：
```text
User Request
  ↓
Instruction Priority (检查优先级)
  ↓
Task Router (确定 Task Type)
  ↓
Project Context Gate (读取已有规范与代码)
  ↓
Preflight (锁定修改范围)
  ↓
Select Workflow (加载指定工作流)
  ↓
Load Required Rules Only (加载必要规则)
  ↓
Minimal Implementation (最小化实现)
  ↓
Targeted Verification (定向验证 Level 1)
  ↓
Risk-Based Broader Verification (风险逐级扩大)
  ↓
Browser Evidence When Required (证据化浏览器验证)
  ↓
Git Diff Review (检查工作区洁净)
  ↓
Definition of Done (DoD 检查清单)
  ↓
Delivery (交付)
```

### 冻结原则 (Anti-Overengineering)
**禁止无限优化**。如果需求已经满足、测试/类型检查通过、关键状态验证通过、浏览器验收通过、Diff 范围合理且不存在 Blocker，**立即结束任务**。不得借由“还能更漂亮”、“还能再重构”而无休止扩大任务范围。

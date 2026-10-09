# 《五十亩山地之后》Frame 06/24 未知图片 Attempt 权威证据核查（2026-10-09）

## 1. 目的和执行约束

只读交叉检查现有 Generation Attempt MySQL Authority、Episode 队列、历史 worker 生命周期、保留 RAW 及现行非再生恢复准则；**不可**利用 `turn.completed`、余下总预算、成功历史外部 Canary 或主观图片判断来声称 Provider 成功，也不触发新原生 Codex 生图，不修改任何正式 Attempt、Stage、Review、图片文件或预算。

正式主工作区运行命令：

```powershell
python scripts/storyos_production_env.py scripts/storyos_generation_evidence_audit.py --episode "episodes/00_独立篇/05_五十亩山地之后"
```

此只读工具也已从隔离分支以全文件 SHA 对照方式同步到主工作区。它仅输出证据摘要与下一步决策，不具备 Retry、Reserve、Commit 权限。

## 2. 实际结果

| 属性 | Frame 06 | Frame 24 |
|---|---|---|
| Queue | `tech_failed` | `tech_failed` |
| 技术失败代码 | `IMAGE_TOOL_NO_ARTIFACT` | `ASPECT_RATIO_MISMATCH` |
| 正式已消耗 Attempt | 1 | 1 |
| MySQL Authority | `OUTCOME_UNKNOWN` | `OUTCOME_UNKNOWN` |
| 历史 Provider | `opencodex` | `opencodex` |
| 正式结果引用 | 无 | 无 |
| Worker 生命周期文件 | 1 | 1 |
| 保留 RAW 数 | 0 | 1 |
| 非再生恢复可自动执行 | 否 | 否 |
| 拒绝原因 | `unsupported_non_regenerating_failure` | `provider_crop_exception_limit_exceeded` |
| 下一步动作 | `VERIFY_PROVIDER_TERMINAL_EVIDENCE` | `VERIFY_PROVIDER_TERMINAL_EVIDENCE` |

Frame 24 的比例偏差约 **0.666666667**，超出可自动修正范围，不可以拉伸/裁切来伪装通过正式图片合同。两个历史 worker 的日志虽有 `turn.completed`，但仅能证明进程层曾正常结束，不等于 Provider 成功提交。状态保持 `OUTCOME_UNKNOWN`。

## 3. 保留的正确门禁

- `next_action` 仍输出 `VERIFY_TECHNICAL_GENERATION_EVIDENCE`，`hard_stop=true` 和 `auto_recoverable=false`，并点名 Frame 06/24。
- Attempt Authority 第 1 次消费仍为 `OUTCOME_UNKNOWN`；`retry_tech` 不会因为剩余 budget 而重新派发第 2 次付费执行。
- `StoryOSRuntime` 为 Running，正式 MySQL 为 `127.0.0.1:3307/STORY_OS_RUNTIME`，`StoryOS-OpenCodex-Proxy` 为 Disabled；禁止恢复代理。
- 现有 Episode 可用正式图片仍为 **2/25**；本轮无新增正式图片、无 Stage 晋级。
- 新增只读工具测试覆盖 UNKNOWN、RESERVED、DISPATCH_COMMITTED、缺回执和已失败但仍需单独审核入场等分支。禁止通过报告本身获得重试许可。

## 4. 后续可以合法推进的动作

1. 对旧 Provider 的真实回执或原始结果引用进行**只读**复核；仅由正式 Authority 的有权限流程、在身份与不可变证据完整时变更终态。不能直接 `UPDATE TB_GENERATION_ATTEMPT` 或删除消费记录。
2. 另行完成固定身份、独立 3306/`STORY_OS_RUNTIME`、TEST_ONLY 的原生 Codex Capability Canary。旧测试库已有的 12 条成功外部 Attempt 不属于本次固定 Canary，不可复用作为证明。
3. 若 Provider 最终结果不可证明，必须保留 UNKNOWN 并决定新的正式合法资产身份/受审替代流程；不得冒充原调用失败、擅自恢复已消费预算。

## 5. 验证和发布范围

- 直接对正式工作区运行只读脚本成功，Frame 06/24 返回 2 条 `VERIFY_PROVIDER_TERMINAL_EVIDENCE`。
- 主工作区相关回归 **16 passed**，隔离分支相关回归 **23 passed**；`git diff --check` 通过。
- 主工作区仍有其他人的未提交修改，因此脚本/测试文件为新增的安全同步文件，正式主分支不强行提交或合并。
- **StoryOS 是图文系统**：不引入视频生成。

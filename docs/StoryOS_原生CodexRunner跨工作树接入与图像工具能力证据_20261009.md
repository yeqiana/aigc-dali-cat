# StoryOS 原生 Codex Runner 跨工作树接入与工具能力证据（2026-10-09）

> 本文只记录已经检查到的事实，不能代替图片工具 Capability Authority、Episode Stage 审核或正式生图。

## 原生通道健康与执行环境

- WebCodex Host 在 Windows Session 0（非交互用户）；该会话 `codex login status` 为 `Not logged in`。不允许因它而将 CODEX 强制改为 direct，也不允许回退到 OpenCodex。
- 本机交互式 Session 1（已有用户桌面）中，原生 `codex_user_runner.py` 进程已经在线。官方 `health --json` 返回 `codex_available=true`、`codex_home_accessible=true`、`codex_auth_present=true`，CLI `codex-cli 0.153.4`。Runner 无模型任务运行。
- 原有集成工作树的客户端默认只找本工作树的 `runtime/codex-user-runner/endpoint.json`，因而错误报告 `LOGIN_AUTH_RUNNER_UNAVAILABLE`；这不是主工作区真实 Runner 下线。
- `codex_user_runner.endpoint_path()` 已在隔离集成分支增加**同一仓库 Git worktree**的安全端点发现：先使用本地端点；仅在 `.git` 为合法同仓库 worktree 指针、工作树位于主仓 `.worktrees` 下时读取主工作区已有端点。绝不复制令牌到 worktree，也不信任任意外部项目端点。
- 用真实在线 Session 1 Runner 进行只读 `runner_health()`，工作树修复后返回健康，并验证 `codex_auth_present=true`。3 条专门测试覆盖同仓发现、禁止跨仓端点、被 Mock 的测试独立端点不泄漏到真实 Runner。

## 真正的生图工具能力仍未证实

- 通过已经接通的原生 Runner 调用真实 `image_payload_transport.payload_capability_preflight`（`quality=high`），返回：
  `status=BLOCKED`；`provider=codex_subscription`；`failure_class=LOGIN_AUTH_IMAGE_TOOL_CAPABILITY_UNKNOWN`；`failure_stage=tool_capability_attestation`；`tool_capability_state=UNKNOWN`。
- 真实登录模型目录可见 56 个条目，但**模型目录可见不等于原生会话已证明拥有 image_generation 工具**。此次 `image_attempt_authority_called=false`、`image_generation_called=false`；不得人为把 UNKNOWN 转 PASS。
- 继续生产需要有可核验的原生 image_generation 工具证据／授权的 TEST_ONLY Capability Canary；在此之前正式图片生成必须保持 BLOCK。
- 不强制使用 Session 0 直连，不使用第三方代理，不将原有 OpenCodex 作品冒充新原生作品。

## Frame 06／24 的正式 Attempt

- Frame 06 的旧工作日志出现 `turn.completed`，但未获得可使用的图片 Artifact。Frame 24 原始图片尺寸与正式画布比例不匹配，现有非再生恢复被拒绝（`provider_crop_exception_limit_exceeded`）。
- V2 `TB_GENERATION_ATTEMPT` 仍有 5 条，包含 2 条历史 `OUTCOME_UNKNOWN`（Frame 06、24），均由旧 OpenCodex Provider 留下。进程结束本身不构成 Provider 调用最终结果证据，不能擅自变更 Authority。
- 新增保护：`next_action` 不再把 UNKNOWN 宣告为可自动重试，`retry_tech` 底层也要求上一 Attempt 确有 `FAILED_AFTER_DISPATCH` 回执。即使剩余图片预算为正，也不可以重复派发未知执行。

## 集成与发布边界

- 本轮修复只进入 `storyos-main-integration-20261009`。主分支 `story-platform-v3-rever` 仍有 133 条工作区改动；不直接强合并、reset、rebase、clean，不触碰现有图片及产物。
- MySQL 3307 大小写兼容复制已于本轮按 27 表、4,380 行哈希对账成功；大写 V2 库此后有独立的新审核生命周期记录，旧小写库仍保留、不自动双向同步。
- StoryOS 是图文生产系统，任何流程均不引入视频生成。

# 《五十亩山地之后》四槽位续产准入与原生 Codex 交接

核验时间：2026-10-09。仅是**交接审计记录**，不是 Provider 成功回执、正式 Production Gate 或生图授权。

## 槽位①：原始 Provider 证据，未解锁
- 队列 Frame 06：`OUTCOME_UNKNOWN`，上一 Provider=`opencodex`，技术码 `IMAGE_TOOL_NO_ARTIFACT`，没有 RAW，没有找到可绑定的 Provider 终态回执。
- 队列 Frame 24：`OUTCOME_UNKNOWN`，上一 Provider=`opencodex`，技术码 `ASPECT_RATIO_MISMATCH`，存在 `media/raw/24-1791474277.png`，MySQL 中能找到对应哈希的 `RECORDED` 记录，但缺少原始 Attempt/Request 的绑定。RAW+RECORDED 不是 Provider 终态证明。
- 二者均消耗过一次真实 Attempt。只读证明：`scripts/storyos_generation_evidence_audit.py` 与 `scripts/storyos_generation_terminal_dossier.py`；调度计划的 `authority_blocked` 恰为这两帧，`ready=[]`，`requires_evidence_verification=true`。
- 未找到正确的原始 Provider 终态证据前必须保持 `UNKNOWN`；禁止复用新 Runner 给旧 OpenCodex Attempt 伪造结果；禁止无条件 `retry-tech`、`init --force`、清空或迁移 MySQL Attempt。

## 槽位②：代码/Runtime
- 已远程合并的 `story-platform-v3-rever`=`7a096c7`（PR #4）。
- 本地原主目录在 `fae8d2e` 时有 3 个独立提交；其 Runtime Launcher、Worker、Exporter 和 Codex User Runner 进程还在运行，不能在其运行时原地热替换代码。
- 已在**隔离 worktree** `.worktrees/storyos-five-mu-production-preflight-20261009` 将本地与远端合并成 `64c5934`，两侧提交均为祖先。专项测试 43 passed、契约检查通过、Doctor 0 错误/0 警告。尚未同步原主目录或重启 Runtime。
- 生产时的 MySQL 配置只来自项目本机 `.storyos/runtime-launcher/runtime.env`（不得输出任何密钥）。不要将隔离 worktree 的测试环境替代为正式 Provider/Attempt Authority。

## 槽位③：Visual Lock
- 锁定分镜和 25 条图片 Prompt 已存在；`media/approved/01.png` 已保存，`media/candidates/scheduled/05-7fd31f8e7be6-a1.png` 是现有候选，`media/raw/` 有四个历史文件。
- 正式 Stage 仍是 `STORYBOARD_LOCKED`；生成帧投影=2、内容 PASS=1、待 Review=1；正式 Production Gate=`pending`，publish=`hold`。
- 11 条当前队列记录属 Visual Lock 历史任务（3 generated、2 tech_failed、6 superseded），**不是** 25 帧正式 Production Queue。正式 Driver 状态 `NEVER_STARTED`。
- 先核验已有 Frame 01/05 的可复用性、真实 Review 与 Visual Lock 权威门禁，再做 Production；不要重新生成已批准图片。

## 槽位④：原生 Codex 交接
- StoryOS 固定：`production.mode=COLLABORATIVE`、`execution.workspace.provider=webcodex`、`execution.image.executor=CODEX`、`execution.vision_review.executor=CODEX`，最多 5 个**在途**图片任务，首个真实恢复阶段建议只允许 1 帧且必须经过完整门禁。
- 本机 `codex-cli 0.153.4` 存在，但 `codex login status` 返回 `Not logged in`。必须由操作者在本机完成正式原生 Codex 登录，再只读验证实际图像工具可用；登录不自动证明图片工具可用。
- **绝不**切换到 OpenCodex (10100)、其他代理、伪造 Runner、fixture、dry-run 代替正式产出；StoryOS 是图文系统，不引入视频生成。
- 在 Frame 06/24 的原始 Provider 终态仍不可验证时，**不可**执行：
  `story_os.py driver start <episode> --resume`
  `image_scheduler.py run <episode>`
  `image_scheduler.py retry-tech <episode>`
- 等原生能力、MYSQL Authority、Visual Lock 与正式 Gate 全部通过且 06/24 已获合法裁决后，再使用本机生产包装器按 canonical Driver resume，并验证第一帧的原生 Provider 完整回执、RAW、Review、MySQL Attempt 原子记账；不能把沙箱通过当作正式生产完成。

## 本轮只读命令（在项目主目录执行）

```powershell
python scripts/storyos_production_env.py scripts/storyos_generation_evidence_audit.py --episode "episodes/00_独立篇/05_五十亩山地之后"
python scripts/storyos_production_env.py scripts/storyos_generation_terminal_dossier.py --episode "episodes/00_独立篇/05_五十亩山地之后"
python scripts/storyos_production_env.py episodes/_system/image_scheduler.py plan "episodes/00_独立篇/05_五十亩山地之后"
python scripts/storyos_production_env.py episodes/_system/next_action.py show "episodes/00_独立篇/05_五十亩山地之后"
python scripts/storyos_production_env.py episodes/_system/story_os.py driver status "episodes/00_独立篇/05_五十亩山地之后" --json
codex login status
```

如任一步出现 Authority 不一致、证据缺失、未知原生工具能力，必须停止发图并报告阻断、路径与可复核证据。不得自行把 `OUTCOME_UNKNOWN` 改写成成功或失败。


# StoryOS 正式生图 UNKNOWN 终态证据包与核销边界（2026-10-09）

## 目的

针对《五十亩山地之后》 Frame 06 / 24 的旧 `OUTCOME_UNKNOWN` 耗费：**只读**建立从 MySQL Attempt、Queue、原始 worker 生命周期与 Codex 控制器日志、Provider Receipt（如存在）、RAW 文件到哈希的逐帧索引。报告不能把 `turn.completed` / worker `FAILED` / Provider RAW 任何单独一项变成 Generation Success、Generation Failure Authority 或自动重试权限。

运行：

```powershell
C:\Users\79873\AppData\Local\Programs\Python\Python312\python.exe scripts/storyos_production_env.py scripts/storyos_generation_terminal_dossier.py --episode "episodes/00_独立篇/05_五十亩山地之后"
```

代码：`scripts/storyos_generation_terminal_dossier.py`，回归：`tests/system/test_storyos_generation_terminal_dossier.py`。

### 正式 3307 MySQL + 原始本地日志实际观察

| 观察项 | Frame 06 | Frame 24 |
|---|---|---|
| Queue | `tech_failed` | `tech_failed` |
| MySQL Attempt | `OUTCOME_UNKNOWN` | `OUTCOME_UNKNOWN` |
| 旧 Provider | `opencodex` | `opencodex` |
| Authority RESULT_REF | 不存在 | 不存在 |
| 原始 Codex worker JSONL | `turn.completed` | `turn.completed` |
| worker lifecycle | `FAILED` | `FAILED` |
| lifecycle generation_key 匹配 Attempt | 是 | 是 |
| RAW 文件 | 0 | 1；2,201,062 bytes |
| Provider Receipt | 未定位 | **MySQL 中定位成功** |
| Provider Receipt 与 RAW | 无法验证 | Frame 24 和 RAW SHA **匹配** |
| Provider Receipt normalize_decision | 无 | `ASPECT_RATIO_MISMATCH` |
| 非生图恢复 | 不支持 | 比例超出 exception crop 上限 |
| 自动重派许可 | **否** | **否** |

Frame 06 原始 controller 日志 SHA：`3cee71a0fc22b27b0ad3c1d75437665f4e41d38f3cdc32350b608c6fd8c77407`。
Frame 24 原始 RAW SHA：`2e1607ac5e637c196336bba95ca72c1879cd40cdda26298501bc6984ce5a2921`。
上述数据来自真实正式 MySQL 和工作区，只读，没有增添 Attempt、没有模型调用。

## 安全处置策略

1. Frame 06：需要找到能够按 Episode/Logical Asset/Generation Key/Attempt Index 绑定的 **Provider 终态执行证据**。控制器 `turn.completed` 仅说明控制器工作结束，不能证明图像 API 未调用或明确失败；没有 RAW 不等于已收到 Provider FAIL。
2. Frame 24：尽管保存了实际 Provider Receipt + RAW，官方 `image_blocked_recovery.inspect_item` 判定 `provider_crop_exception_limit_exceeded`。不能为赶进度调高裁切异常边界、改变 SHA 或将不匹配尺寸图强行认作 M00 正式合格图。应核销原始 Provider 调用的实际终态与对应 Generation Authority，然后经独立重试准入重新决定是否进行新的原生 Codex Attempt。
3. 两帧当前 **只可查证，不可自动重试**。若过去的 `OUTCOME_UNKNOWN` 最终被受审处置，必须有不可变终态证据、独立执行审计和共享 MySQL 次数维护；不能直接 UPDATE DB、删除旧 Attempt、伪造 `FAILED_AFTER_DISPATCH` 或退款。
4. 旧 Provider `opencodex` 不能再次接入；StoryOS 是图文，不生成视频。所有未来实际图片生产仍须经原生 Codex capability 和 Canonical Production Gates。

## 本轮测试与界限

- 第一轮：Runner/Canary/Review/UNKNOWN 专项三组 55 passed；新增脚本最初导入路径失败，已修正。
- 增强 Provider Receipt 绑定信息后的独立测试覆盖：查找 MySQL Receipt、Frame 和 RAW SHA 匹配、不匹配时 fail-closed，以及 `turn.completed` 不产生成功判定。
- 第二轮隔离分支四槽位专项：16+9+11+18 = **54 passed**（导入与新插入产生的收集失败已纠正，Provider 组最终 **16 passed**）。
- 主工作区实际正式 Episode 只读运行成功，相关 **23 passed**。
- TEST_ONLY Phase5A Epoch 2 维持 `queued/0/2`，未调用图片 Provider；没有突破上轮安全检查拦截。

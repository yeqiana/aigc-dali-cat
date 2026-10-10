# StoryOS 原生 Codex 人物契约 CAS / Story 成果复用审计（2026-10-10）

## 证据与目标

2026-10-10 已核验原生 codex-cli 为 0.162.1，主工作区针对新版 \`00-06_五十亩山地之后\` 的原生 \`plan\` 只读结果为 \`READY_TO_START\`，有效工作模式 CODEX_MANAGED，图片执行器 CODEX，MySQL 当前阶段 IDEA_LOCKED，未决 UNKNOWN/活跃 Attempt 为 0，Driver NEVER_STARTED。此结果**不是**文本模型、图像工具权益或整集 \`PUBLISH_READY\` 的证明。

PR #34 已解决 Worker 读错 JSON 权威和普通的 Review Lock，但仍存在跨进程版本更新的 TOCTOU 空隙。下一轮改造：

1. CAS：在 MySQL \`TB_EPISODE_CONTRACT\` 的同一事务内 \`SELECT ... FOR UPDATE\` 检查最新 SHA，再使用纯 INSERT 追加一条新版本。不再在 reviewed Story Lock 路径使用 Legacy UPSERT。
2. 恢复诊断：只读 \`scripts/storyos_creative_recovery_readonly.py --episode episodes/...\`，结合正式人物契约、真实 Story 文件 SHA 和 Provider 回执给出结构化结果。
3. 回归测试：从独立测试 Episode + 假 SQL 连接验证成功、过期、版本冲突、空记录、无复核、SHA 漂移、幂等和防伪；不得向正式 MySQL 写数据。
4. 集成：仅在四槽 Git worktree 中验证并经 CI 合并；不覆盖本地尚未同步的主工作区或正式图片资产。

## 为什么修复 CAS

旧 \`reviewed_story_lock()\` 虽然在保存前再读 SHA，但另一进程仍可能在“最后一次读”之后先插入新版本。若接着调用会无条件 UPSERT 的 \`save_version()\`，旧 Worker 可基于失效的 DRAFT 继续提交。

新 \`save_version_if_latest(record,expected_sha256)\` 使用**同一个事务**中的最新版本读锁和新增版本插入，失败即回滚。数据库唯一 \`(EPISODE_ID, CONTRACT_TYPE, VERSION_NO)\` 索引再次防止重号。原有非 Review 版本保存路径保持兼容。

## 恢复诊断不意味着自动生成

只读检查只会给出如下事实状态：
- \`MODEL_SUCCEEDED_BUT_STORY_REVIEW_MISSING\`：存在成功模型回执，但不足以推进 Story Lock；优先核实已有创作成果与审核产物。
- \`REVIEW_EVIDENCE_PRESENT_CAN_ATTEMPT_CANONICAL_LOCK\`：Story 文件及基本 SHA/理由均在；仍需正式校验并由已有合法 Writer 提交。
- \`REVIEW_STORY_SHA_DRIFT\` / \`REVIEW_CONTRACT_SHA_STALE\`：不允许直接复用旧证据。
- \`CONTRACT_ALREADY_LOCKED_VERIFY_STORY_GATES\`：仅人物契约锁定，不表示 Storyboard Lock。
- \`CHARACTER_AUTHORITY_UNAVAILABLE\`：数据库查询异常必须 fail-closed，不得回退本地历史 JSON。

\`storyos_codex_managed.py plan\` 会附带 \`creative_story_recovery\` 说明，但模型权益与最终审核仍显示为未实证。用户若确认启动正式生产，只可由原生 Codex 在正式独占 Episode Owner 下执行；WebCodex 不得代为启动第二个 Driver，工程工作树亦不得持有真实 MySQL 凭据副本。

## 测试与合并要求

- \`python -m pytest -q tests/platform/test_mysql_episode_contract_cas.py tests/platform/test_mysql_episode_contract_repository.py\`
- \`python -m pytest -q tests/system/test_storyos_creative_recovery_readonly.py tests/system/test_character_reviewed_story_lock.py\`
- \`python -m pytest -q tests/system/test_character_contract_authority.py tests/system/test_storyos_native_codex_full_auto_entry.py tests/system/test_storyos_native_model_readiness.py\`
- 测试与 CI 全部通过后合并远端 \`story-platform-v3-rever\`；主工作区安全同步必须由当前 Writer 确认退出后执行。

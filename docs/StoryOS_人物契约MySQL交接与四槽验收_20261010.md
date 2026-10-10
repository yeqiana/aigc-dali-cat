# StoryOS 人物契约 MySQL 交接与四槽验收（2026-10-10）

## 观察到的故障

新版 00-06 的 CREATIVE_STORY 曾连续四次 BLOCKED，而 story.authoring Provider 回执均为 SUCCESS。
后置检查的两条错误为：
- character contract status must be LOCKED before Story Lock
- NO-ANOMALY TEST must be rechecked_against_final_story=true before Story Lock

生产契约已用 episode_contract_persistence 接入 MySQL Authority，因此 mysql 模式可以没有 meta/character-contract.json；旧模型指令仍要求直接改此文件。

## 四槽分工

- 槽位 1：人物契约的正式 review-lock 写入 API 和 show --with-sha，只由 Episode 合法生产 Owner 使用。
- 槽位 2：原生 Codex Story Worker 改为读取 Capsule 或 show 的权威数据，并按最终故事证据使用 review-lock，不再要求直接编辑 JSON。
- 槽位 3：用临时 Episode 与模拟契约持久化测试 SHA 变化、无复核、不一致、重复提交等拒绝条件。
- 槽位 4：在独立集成分支汇总代码、执行测试、安全合并，留下验收边界。

## Worker 提交的复核文件

Story Worker 在保存真实最终故事后填写 meta/character-story-review.json：

    {
      "schema_version": 1,
      "expected_contract_sha256": "<当前 show --with-sha 显示的真实权威 SHA256>",
      "story_path": "docs/story.md",
      "story_sha256": "<最终故事文件真实 SHA256>",
      "no_anomaly_test": {
        "pass": true,
        "ordinary_day_plan": "说明删除异常后原本如何正常行动",
        "review_reason": "至少 20 个字符，针对实际最终故事解释生活动机"
      }
    }

若最终故事人物、动机或场景确有变化，可以提交完整的 proposed_contract，但不允许更改 origin 的 schema_version、created_at、selection_seed、world_identity。

随后正式调用：

    python episodes/_system/character_contract.py show "<episode>" --with-sha
    python episodes/_system/character_contract.py review-lock "<episode>" --review meta/character-story-review.json
    python episodes/_system/character_contract.py validate "<episode>" --require-locked

review-lock 仅提交人物契约，不能推进 Episode stage，也不能授予 Review Authority、Generation Attempt 或视觉 PASS。模型自述的复核不等于人工审核；仍由既有 Story Gate 进行后置校验。

## 必须通过的拒绝边界

- 最终故事不存在、过短、超出 Episode 目录、字节 SHA 漂移 -> BLOCKED，绝不提交。
- 旧合同 SHA 与当前 MySQL Authority 不一致 -> BLOCKED。
- 无异常复核缺失、否定结果或空泛理由 -> BLOCKED。
- 当前合同已经 LOCKED 且来源相同 -> 只读 ALREADY_LOCKED，不追加新版本；来源冲突 -> BLOCKED。
- 合同候选未通过现有普通人物分数及其它校验 -> BLOCKED。
- 不直接修改 runtime.env、生产库、00-06 现有资产，不创建新 Driver，不启动 Codex paid worker。
- 旧版本没有 final_story_review 的 LOCKED 合同仍按既有兼容规则验证，避免重写历史。

## 验收顺序

1. Python 单测对 review-lock 的路径、SHA、review、只提交一次的行为进行覆盖。
2. 检查现有 Character Contract、Story Worker 与 Runtime DAG 的回归。
3. CI 通过并主线合并后，正式生产 Owner 再核对 00-06 的有效已有成果，避免重复调用已成功的付费模型。
4. 正式 MySQL 写入和完整 STORYBOARD_LOCKED 验收属于另一次授权执行；本 PR 不宣称已经完成。

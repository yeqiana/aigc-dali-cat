# StoryOS Production Profile Freeze — 2026-09-19

状态：**FREEZE CANDIDATE / JSON-FILE AUTHORITY / MYSQL-REDIS DEFERRED**  
适用分支：`story-platform-v3`  
最近提交基线：`bd693905130e50f85cad567730c508f7712c77e6`  
当前工作树：**DIRTY，尚未具备 SLO 运行资格**

## 1. 冻结目的

为后续 3-Episode Production SLO 提供不变的运行基线。本冻结只确认当前实际读取路径，不宣称 MySQL/Redis 已切为生产权威。

## 2. 有效配置

| 项目 | 冻结值 | 证据 |
| --- | --- | --- |
| platform version | `2.6.1` | `story_os_manifest.json` SHA-256 `17e3be3a03ec2304251e4d6a5c9a59f92ad6784ccdbe8c09c0134da937deec8f` |
| episode metadata authority | `json` | `config/storyos.yaml` `storage.episode_meta_store.mode` |
| hot-state authority | `file` | `config/storyos.yaml` `storage.hot_state.mode` |
| runtime trace store | `jsonl` under `.storyos` | `config/storyos.yaml` `storage.runtime_store` |
| authoring/review runtime | `WORK` | `config/storyos.yaml` / runtime contract |
| image execution route | configured provider router; no `OPENAI_API_KEY` in current process | `config/providers/image-provider-runtime.json` + environment probe |
| image provider runtime contract | `gpt-image-2.5-flare`, per-frame review required | provider runtime JSON |
| API/runtime override | none detected for storage or runtime mode | current process environment probe |

## 3. 配置指纹

- `config/storyos.yaml`: `6a540733ba200103a5ca7fc664bbae46af53a32978358c125682df37eb9da395`
- `config/providers/image-provider-runtime.json`: `4a60f219d2408be60911833e0feb449496a2eba992182f37f5b283ef42263dc8`
- Web Console 文件当前处于用户改造工作树，**不纳入本次生产引擎 SLO profile**；其构建结果单独验收。

以上指纹只能组成候选 Profile。只有在生产相关代码、配置和 Episode 运行证据形成干净且可复现的提交后，才可转为正式 provenance。任何生产路径、provider、并发、Review 策略或存储模式变更，都必须新建 Profile 并重新开始样本统计。

## 4. 冻结边界

- 本轮 SLO 期间不得把 `episode_meta_store` 改成 `dual`/`mysql-only`；
- 本轮 SLO 期间不得把 `hot_state` 改成 `dual`/`redis`；
- MySQL/Redis authority 继续保留测试和迁移能力，但标记为 **DEFERRED**；
- 未授权时不运行真实图片、发布或外部平台回写；
- Episode state 仍只能由 `meta/episode-state.json` 作为阶段事实源。

## 5. Profile 验证结果

- `python scripts/phase9_production_switch.py status`：V3 ownership `EFFECTIVE`；
- `python episodes/_system/story_os_doctor.py`：`errors=0 warnings=0`；
- `python episodes/_system/contract_sync.py`：V2.6.1 contract sync PASS；
- `pytest tests/system/test_phase9_report_governance.py`：`3 passed`；
- Python platform/system 全量回归：`1675 passed, 1 skipped`；
- 当前 Episode 状态：`PUBLISH_READY=4`，但 `PRODUCTION_PASSED/PUBLISHED/DATA_REVIEWED=0`。

## 6. 结论

F0 的“当前路径明确”证据已形成，F1 仍为候选状态，原因是工作树不洁，不能把最近提交 SHA 冒充当前代码快照。这不等于 G0/G1 通过。下一步先完成生产相关改动的可复现基线，再在该 Profile 下完成 3 篇全新 Episode 的真实 `create --full-auto → PUBLISH_READY`，并记录完整 wall-time、图片、Review、repair、人工介入和发布后反馈证据。

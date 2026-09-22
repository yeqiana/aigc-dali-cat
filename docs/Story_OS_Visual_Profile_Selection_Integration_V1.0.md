# Story OS Visual Profile Selection Integration V1.0

- 文档状态：接入设计稿（Design Only，Visual Profile Governance Phase 3.4）
- 前置：Phase 3.1 Selector 设计、Phase 3.2 Contract、Phase 3.3 Rule Engine
- 本阶段不接入生产：不修改 machine_gate、不改 frame_contract、不改 production runtime、不自动生产 Episode
- 目标：定义 Selector 输出如何被 Visual Lock 消费，为 Phase 3.5 Gate 校验铺路

---

## 1. 目标与边界

本阶段只回答一个问题：Selector 已经能产出"选哪个 + 证据"，接下来**谁**、**在什么时候**、**用什么结构**把它固定下来。

链路：

```text
Story Intent + Episode Context + Audience Expectation
        |
        v
Visual Profile Selector            (episodes/_system/visual_profile_selector.py)
        |
        v
Selection Evidence                 (selector-evidence.schema.json)
        |
        v
Visual Lock                        (本文件定义：profile_id + selection_evidence + confirmed_by + confirmed_at)
        |
        v
Frame Contract
        |
        v
Production
```

边界：

- Selector 只产出建议与证据，不落盘、不改 Episode。
- Visual Lock 是**人确认后**的固定点；没有人工确认，Selector 的 selected 也只是一个候选事实。
- Frame Contract 与 Production 不在本阶段改动，只是下游消费者。

---

## 2. Visual Lock 记录契约

Visual Lock 需要保存的最小记录：

```json
{
  "schema_version": 1,
  "profile_id": "M01_ANCIENT_MUNDANE_LIFE_V1",
  "profile_path": "standards/visual_profiles/profiles/M01_ANCIENT_MUNDANE_LIFE_V1.json",
  "selection": "selected",
  "selection_evidence": {
    "selector_version": "1.0",
    "source": "rule_engine",
    "registry": "standards/visual_profiles/index.json",
    "inputs_digest": "sha256:...",
    "inputs_summary": {},
    "matched_rules": ["world=historical_real", "era=ancient"],
    "rejected": [{"profile": "M03_JIANGNAN_IMMERSIVE_LIFE_V1", "reason": "not matched: location=jiangnan, experience_type=immersive_first_person"}],
    "reason": ["prio=semantic"]
  },
  "confirmed_by": "user_or_delegated_approver",
  "confirmed_at": "2026-09-11T00:00:00Z",
  "confirmation_mode": "direct_user | delegated_auto"
}
```

字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| profile_id | 是 | 必须已注册且 active；未注册即非法 |
| profile_path | 是 | registry 声明的路径，写入时校验文件存在 |
| selection | 是 | selected / needs_confirmation 被人工裁决后的最终结果 |
| selection_evidence | 是 | 直接引用 Selector 输出的 evidence，不得手写或改写 |
| confirmed_by | 是 | 确认者标识；auto 派发必须区分 delegated_auto |
| confirmed_at | 是 | 确认时间（UTC ISO8601） |
| confirmation_mode | 是 | direct_user 或 delegated_auto，用于 Gate 判断证据强度 |

原则：Visual Lock 保存的是**选择事实 + 确认事实**，不是分数，也不是 prompt。

---

## 3. 与现有权威的关系（不新增状态机）

接入不新造通道，Visual Lock 结果进入既有三处之一：

1. Episode meta `meta/visual-profile.json`：Episode 级显式锁定，`visual_profile_bridge_v224.episode_meta()` 已消费。
2. `meta/story-gates.json` 的 `visual_profile`：mode=override 时由 `resolve_base_profile()` 消费。
3. Selector 证据建议写入 `meta/runtime-request.json` 的 `visual_profile_selection`（派生证据），不改写既有 `visual_profile` / `visual_profile_resolution`。

权威顺序保持现状：Episode meta 与 story-gates override 的一致性与冲突处理不变（冲突仍硬失败 VISUAL_PROFILE_AUTHORITY_MISMATCH）。Visual Lock 只是把 Selector 的结论写进上述通道，不新增第四权威。

---

## 4. 人工确认路径

Selector 的三种结果与后续动作：

| Selector status | Visual Lock 动作 |
| --- | --- |
| selected | 可作为确认候选；仍需记录 confirmed_by/confirmed_at |
| needs_confirmation | 禁止自动落盘；必须人工在候选集中裁决后再写 Visual Lock |
| defaulted | 按默认 M00 记录，但必须保留 reason（no_rule_matched） |
| rejected | 不落盘；修正输入或强制指定后再走一次 Selector |

冲突（例如"古代 + 江南"同时命中 M01 与 M03）由人工裁决，Selector 不猜、不按优先级静默取一。

---

## 5. 写入时机与不可变性

- 写入时机：Episode 进入 Visual Lock 之前（即 Frame Contract 编译之前），人确认后一次写入。
- 不可变：已锁定的 Visual Lock 不得被 Selector 重写；如需变更，必须走新的确认记录并保留历史。
- 历史兼容：不迁移历史 Episode 的 profile 绑定；无 selection_evidence 的旧 Episode 不因此失败（与 Phase 2.x / W-21 历史兼容策略一致）。

---

## 6. 失败与兼容策略

- 未注册 profile_id：fail-closed，禁止写入 Visual Lock。
- evidence 缺失或 inputs_digest 不匹配：拒绝写入（配置存在 ≠ 选择事实存在）。
- registry 不可读：拒绝写入，不降级为默认。
- 旧 Episode：没有 Visual Lock / selection_evidence 时不补造、不阻断。

---

## 7. Phase 3.5 Gate 边界（设计预告，不实现）

Phase 3.5 的 Gate 只校验"选择证据存在且自洽"，不改生产调度：

- 若 Episode 声明需要 Selector 证据：校验 presence + profile_id 已注册 + inputs_digest 格式合法 + confirmed_by/confirmed_at 存在。
- 不校验"选得对不对"（那是人工裁决），不重算 specificity，不产生分数。
- needs_confirmation 未被人工裁决就进入下游：FAIL。
- 历史 Episode 无标记：SKIP，不误伤。

---

## 8. 本阶段结论

Selector 已可运行并可验证（Phase 3.3）；本文件只定义它如何被 Visual Lock 消费。**不接入生产**：Frame Contract、machine_gate、production runtime 均未修改。Phase 3.5 才考虑 Gate 校验。

---

## 9. Phase 4.1 接入状态：Visual Lock Runtime Adapter

- 实现：`episodes/_system/visual_profile_lock_adapter.py`
- 接入点：`episodes/_system/story_creator.py::create_episode()`
- 产出：`<episode>/meta/visual-profile.json`（Visual Lock **草稿**，不是锁）

第 3 节列出的三条视觉权威路径中，第 1 条（Episode meta）现在真正由创建流程写入：

```text
Story Intent / Episode Context / Audience Expectation
        |
        v
visual_profile_selector.select(strict=True)     失败即失败，不静默兜底
        |
        v
create_visual_lock_draft()                      原样复制 selection_evidence
        |
        v
meta/visual-profile.json                        SELECTED / NEEDS_CONFIRMATION
```

生命周期（本阶段只写前两态）：

```text
DRAFT -> SELECTED -> NEEDS_CONFIRMATION -> LOCKED -> FROZEN
```

- `selected` / `defaulted` → `SELECTED`：写明 `profile_id` 与 registry `profile_path`。
- `needs_confirmation` → `NEEDS_CONFIRMATION`：**不写 profile_id**，候选留在 `selection.candidates`。
- `rejected` → 创建失败，不落任何文件（Selector 在写盘前 fail-closed）。

草稿不是锁：草稿的 `confirmation_mode="pending"` 不在 Phase 3.5 锁契约允许集内，因此
`visual_profile_lock.validate_visual_profile_lock()` 对草稿必定 FAIL；补上 Phase 4.2 的
`confirmed_by` + `confirmed_at` 与合法 `confirmation_mode` 后，同一份文档即可 PASS。

兼容与边界：

- 已有 `meta/visual-profile.json` 的 Episode：只读，不重新选择，不覆盖。
- 未声明 Story Intent 的一次性创建：Selector 返回 `defaulted`，profile 与升级前一致（registry 默认 M00）。
- 不写 `story-gates.json`、`episode-state.json`、Frame Contract、machine_gate，也不生成图片。
- 已验证的 legacy 视觉层影响（只读探查 visual_profile_bridge_v224）：
  - 默认 M00 草稿与"无 meta/visual-profile.json"相比，compiled prompt contract 仅 1/105 行不同：
    authority=story-gates/default → authority=meta/visual-profile.json；profile_id、profile_sha256、
    全部 visual_dna 行完全一致（governed M00 文档本身也带 42 条 visual_dna）。
  - M01/M02/M03 使用各自的 visual_dna（M01 为 17 条），进入正式生产前需确认纹理密度是否达标。
  - NEEDS_CONFIRMATION 草稿的 profile_id 为空，episode_meta() 会 fail-closed
    （EPISODE_VISUAL_PROFILE_INVALID）。这是刻意的：未裁决的选择不允许进入生产，Phase 4.2
    必须补齐确认记录；当前默认入口（--visual-profile M00）不会触发该路径。

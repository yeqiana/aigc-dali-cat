# Story OS Visual Profile Production Freeze V1.0

Visual Profile Governance Phase 4.5。本文定义 Visual Profile 进入生产后的规则，是 Phase 4.1（Runtime Adapter）、4.2（Lifecycle）、4.3（Production Gate）、4.4（End-to-End Validation）的收口规范。

本文不建立第二权威。与 `standards/制作规范_正式版.md`、`meta/episode-state.json`、`meta/story-gates.json` 冲突时，以既有权威为准；Visual Profile 只负责"这一集用哪个视觉体系"，不改变阶段状态机，也不改变门禁证据职责。

## 1. 定位

Visual Profile 是**生产合同**，不是 prompt。

```text
Story Intent
    |
    v
Visual Profile Selector          (visual_profile_selector.py)
    |
    v
Selection Evidence                (selector-evidence.schema.json)
    |
    v
Visual Lock  meta/visual-profile.json
    DRAFT -> SELECTED / NEEDS_CONFIRMATION     (Phase 4.1 runtime adapter)
    SELECTED / NEEDS_CONFIRMATION -> LOCKED    (Phase 4.2 lifecycle confirm)
    LOCKED -> FROZEN                           (Phase 4.2 lifecycle freeze)
    |
    v
Production Gate                   (visual_profile_gate.py, read-only)
    |
    v
Production
```

## 2. Lock 原则

**生产开始前，Visual Lock 必须存在，且必须是 LOCKED。**

- 只有 `meta/visual-profile.json` 一个存储位置，不新增第四处。
- 未裁决的草稿（SELECTED / NEEDS_CONFIRMATION）不算锁定，不得进入生产。
- 确认必须由人给出：`confirmed_by` + `confirmed_at`，不允许系统自行落 LOCKED。
- 冲突选择（例如"古代 + 江南"）只产生 candidate 列表，必须由人指定最终 profile，系统不猜。

Gate 检查顺序与错误码：

| 顺序 | 检查 | 失败错误码 |
| --- | --- | --- |
| 1 | profile 在 Registry 中且 active | `VISUAL_PROFILE_NOT_REGISTERED` / `VISUAL_PROFILE_NOT_ACTIVE` |
| 2 | profile_path 与 Registry 一致且文件存在 | `VISUAL_PROFILE_PATH_MISMATCH` / `VISUAL_PROFILE_FILE_MISSING` |
| 3 | 生命周期为 LOCKED（或 FROZEN） | `VISUAL_PROFILE_NOT_LOCKED` |
| 4 | selection_evidence 完整（selector_version / inputs_digest / matched_rules / reason / source） | `VISUAL_PROFILE_SELECTION_EVIDENCE_MISSING` |
| 5 | confirmation 记录存在 | `VISUAL_PROFILE_CONFIRMATION_MISSING` |
| 6 | 发布阶段额外要求 FROZEN | `VISUAL_PROFILE_NOT_FROZEN` |

## 3. Freeze 原则

**生成第一张正式资产后，Visual Lock 必须 FROZEN。**

冻结后禁止修改：

- `profile_id`
- `profile_path`
- capture philosophy、realism 等 profile 内部 DNA（由 profile 文档 SHA 体现）
- 选择证据与确认证据

冻结机制：

```json
{
  "lifecycle_state": "FROZEN",
  "lock_policy": "production_frozen",
  "confirmation": { "mode": "human", "confirmed_by": "...", "confirmed_at": "...", "reason": "..." },
  "frozen": { "frozen_by": "...", "frozen_at": "...", "reason": "...", "inherits_confirmation_by": "..." }
}
```

规则：

- FROZEN 完整继承 LOCKED 的确认记录，不重写。
- FROZEN 之后任何转移都会返回 `VISUAL_LOCK_ALREADY_FROZEN`，且不会写盘。
- 只有带确认记录的 LOCKED 锁才能冻结；否则返回 `VISUAL_LOCK_CONFIRMATION_INVALID`。

生命周期允许/禁止的转移：

| 起点 | 终点 | 结果 |
| --- | --- | --- |
| SELECTED | LOCKED | 允许 |
| NEEDS_CONFIRMATION | LOCKED | 允许（必须指定 candidate 中的 profile） |
| LOCKED | FROZEN | 允许 |
| DRAFT | LOCKED | 禁止 `VISUAL_LOCK_INVALID_TRANSITION` |
| NEEDS_CONFIRMATION | FROZEN | 禁止 `VISUAL_LOCK_INVALID_TRANSITION` |
| FROZEN | 任意 | 禁止 `VISUAL_LOCK_ALREADY_FROZEN` |

## 4. 变更流程

需要更换 Profile 时，**必须新建 Episode 版本，不得覆盖旧生产。**

```text
想要 M01 的 Episode 换到 M03
    |
    v
新建 Episode 版本（新的 Episode 目录）
    |
    v
Selector 重新选择 -> 新 Visual Lock -> 重新确认
    |
    v
旧 Episode 的 FROZEN Visual Lock 保持不变，作为历史事实
```

禁止：

- 修改已 FROZEN 的 Visual Lock。
- 在同一个 Episode 上通过覆盖 `meta/visual-profile.json` 换体系。
- 为"追赶"生产而把 NEEDS_CONFIRMATION 直接当 LOCKED 使用。

## 5. Evidence 原则

任何 Profile 选择都必须可追溯，且是**执行事实**，不是"配置存在"。

- 选择必须带 Selection Evidence：selector 版本、输入摘要 digest、命中的规则、被排除的 profile、选择原因、来源。
- 确认必须带确认记录：谁确认、何时确认、确认模式。
- 冻结必须带冻结记录，并继承确认来源。
- 没有 Evidence 的 Visual Lock 不允许创建；没有确认的锁不允许生产。

## 6. 历史兼容

| 情形 | Gate 结果 | 是否阻断 |
| --- | --- | --- |
| Episode 没有 Visual Lock，也没有 governance opt-in | `legacy_unmanaged` | 否 |
| pre-governance V2.2.4 的 meta/visual-profile.json（无 governance 字段） | `legacy_unmanaged` | 否 |
| Episode 声明需要 Visual Profile（runtime-request 带 visual_profile_selection）但没有锁 | `VISUAL_PROFILE_LOCK_MISSING` | 是 |
| 治理锁但没有确认记录 | `VISUAL_PROFILE_NOT_LOCKED` | 是 |

原则：只约束新生产，不追溯历史 Episode，不自动迁移旧资产。

## 7. 当前接入状态

- Phase 4.1/4.2/4.3/4.4 已实现：Selector 选择、Visual Lock 草稿、生命周期确认/冻结、独立 Production Gate、端到端验证。
- **machine_gate.py 未接入。** 审计确认 machine_gate 当前没有任何 visual hook，因此本阶段只提供 validator 接口（`validate_visual_profile_for_production` / `verify_visual_profile_for_production`），不强行修改 gate。
- 未修改 Runtime、未修改 `episode-state.json`、未修改 `story-gates.json`、未修改 Frame Contract、未重新生产图片。

## 8. 使用方式

```text
# 只读校验（生产阶段）
python episodes/_system/visual_profile_gate.py validate <episode_dir>
python episodes/_system/visual_profile_gate.py verify <episode_dir>

# 发布阶段（额外要求 FROZEN）
python episodes/_system/visual_profile_gate.py verify <episode_dir> --stage release
```

Python 接口：

```python
from visual_profile_lock_lifecycle import confirm_visual_lock, freeze_visual_lock
from visual_profile_gate import validate_visual_profile_for_production

confirm_visual_lock(episode, confirmed_by="...", confirmed_at="...", profile_id=None)
freeze_visual_lock(episode, frozen_by="...", frozen_at="...")
validate_visual_profile_for_production(episode=episode, stage="production")
```

## 9. 明确不做

- 不做图片生产，不做人脸识别/CLIP/向量检索。
- 不自动 learning，不自动调整 Advisor，不自动修改 Lexicon 或 Similarity 权重。
- 不引入评分数值。
- 不把 machine_gate 直接改成强校验（需后续单独决策）。
- 不自动迁移历史 Episode 的 Visual Lock。


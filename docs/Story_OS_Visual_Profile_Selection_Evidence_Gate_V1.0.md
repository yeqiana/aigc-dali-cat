# Story OS Visual Profile Selection Evidence Gate V1.0

- 文档状态：已实施（Visual Profile Governance Phase 3.5）
- 归属模块：episodes/_system/visual_profile_lock.py
- 契约文件：standards/visual_profiles/schema/visual-lock.schema.json
- 测试：tests/system/test_visual_profile_lock.py
- 本阶段边界：不修改 machine_gate、Frame Contract、Story Lock、production runtime；不迁移历史 Episode；不提交运行数据

---

## 1. 目标与边界

Phase 3.3 让 Selector 能够产出「选了哪个 Profile + 选择证据」，Phase 3.4 固定了 Visual Lock 的记录形态。
但在此之前没有任何一处验证这些记录，于是「lock 文件存在」仍然可能被当成「有人、在某时、按某种规则确认过这次选择」。

本阶段只回答一个问题：

    这个 Visual Lock 里的选择事实是否存在，并且自洽？

原则：

    配置存在       不是证据
    选择事实存在   才是证据

Gate 不负责：

    - 重新运行 Selector
    - 重新选择 Profile
    - 自动修正、补齐或改写 Visual Lock
    - 修改 Episode 中的任何文件

链路：

    Selector
        |
        v
    Selection Evidence
        |
        v
    Visual Lock
        |
        v
    Machine Validation   <-- 本阶段新增（独立模块，尚未接入 machine_gate）

---

## 2. Visual Lock Contract

契约文件：standards/visual_profiles/schema/visual-lock.schema.json

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| schema_version | 是 | 固定 1 |
| profile_id | 是 | 必须是 Registry 中 active 的 profile id |
| profile_path | 是 | 必须与 Registry 中该 id 的 path 完全一致 |
| selection_evidence | 是 | Selector 产出的选择事实（照抄，不重算） |
| selection | 否 | 裁定结果 selected / needs_confirmation / defaulted / rejected；也接受对象形态 |
| status | 否 | selection 的等价顶层写法 |
| confirmation_mode | 否 | human / system（另接受 direct_user、delegated_auto，等价于人工确认） |
| confirmed_by | human 模式必填 | 确认人标识 |
| confirmed_at | human 模式必填 | ISO-8601 时间 |

selection_evidence 必须包含：

    selector_version
    inputs_digest      sha256:<64 位十六进制>
    matched_rules      字符串数组（defaulted 允许为空）
    reason             非空（字符串或字符串数组）
    source             例如 rule_engine

示例（M01 场景）：

    {
      "schema_version": 1,
      "profile_id": "M01_ANCIENT_MUNDANE_LIFE_V1",
      "profile_path": "standards/visual_profiles/profiles/M01_ANCIENT_MUNDANE_LIFE_V1.json",
      "selection": "selected",
      "selection_evidence": {
        "selector_version": "1.0",
        "source": "rule_engine",
        "inputs_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        "matched_rules": ["world=historical_real", "era=ancient"],
        "reason": ["prio=semantic"]
      },
      "confirmation_mode": "human",
      "confirmed_by": "reviewer",
      "confirmed_at": "2026-09-12T10:00:00+08:00"
    }

---

## 3. Validator 规则

入口：

    visual_profile_lock.validate_visual_profile_lock(lock=None, *, story_root=None, episode=None, required=None)

检查顺序（首个失败决定 result.code）：

| 顺序 | 检查 | 失败 error code |
| --- | --- | --- |
| 1 | profile_id 已注册 | VISUAL_PROFILE_NOT_REGISTERED |
| 1 | profile 状态为 active | VISUAL_PROFILE_NOT_ACTIVE |
| 2 | profile_path 与 Registry 一致 | VISUAL_PROFILE_PATH_MISMATCH |
| 2 | profile_path 指向的文件存在 | VISUAL_PROFILE_FILE_MISSING |
| 3 | selection_evidence 存在且字段合法 | VISUAL_PROFILE_SELECTION_EVIDENCE_MISSING |
| 4 | 选择已裁定（非 needs_confirmation / rejected） | VISUAL_PROFILE_NOT_CONFIRMED |
| 5 | 人工确认记录齐全 | VISUAL_PROFILE_CONFIRMATION_MISSING |
| 6 | 其余形态问题（schema 子集校验） | VISUAL_PROFILE_LOCK_INVALID |
| - | 声明需要治理但没有 lock | VISUAL_PROFILE_LOCK_MISSING |
| - | lock 文件不可解析 | VISUAL_PROFILE_LOCK_UNREADABLE |

说明：

- 第 3 步只要求选择事实「存在且格式合法」，不判断「选得对不对」；Gate 不重算 Selector，也没有评分或候选排序。
- 第 4 步优先于第 5 步：needs_confirmation 的 lock 即使补齐确认记录仍然不是 locked，必须回到 Selector 重新裁定后重写 lock。
- confirmation_mode 缺省按 human 处理（fail-closed）；system 模式不要求人工确认记录。
- registry 本身不可读时，直接沿用 Registry 自己的 error code（VISUAL_PROFILE_REGISTRY_MISSING / _INVALID），不降级成默认 Profile。

结果结构：

    status      pass | fail | legacy_unmanaged
    code        失败时为首个 error code；pass / legacy 为 null
    required    Episode 是否声明需要 Visual Profile 治理
    governed    该文档是否声明了治理字段
    judged      是否真的执行了校验
    source      lock 来源（仓库相对路径）
    profile_id / profile_path
    checks      每项检查的 pass / fail / skip 明细
    errors      {code, detail} 列表

只读保证：validate 不写任何文件、不改动传入的 lock 对象（测试覆盖）。

---

## 4. 历史兼容策略

| 情况 | 结果 |
| --- | --- |
| Episode 没有 meta/visual-profile.json，也没有治理声明 | legacy_unmanaged（不是 FAIL） |
| 旧 V2.2.4 meta/visual-profile.json（profile_id/profile_path + tool_version/mode，无治理字段） | legacy_unmanaged（不追溯失败） |
| Episode 声明进入治理（governed lock，或 runtime-request 带 visual_profile_selection）但没有 lock | VISUAL_PROFILE_LOCK_MISSING |

判别规则：只有出现下列任一治理字段，文档才被视为 Phase 3.5 Visual Lock：

    selection / status / selection_evidence / confirmation_mode / confirmed_by / confirmed_at

「presence + 旧 tool_version/mode」不构成治理证据，因此历史 Episode 不会被追溯判失败。仓库现有实例：

- episodes/12_千寻/01_那条不存在的隧道/meta/visual-profile.json -> legacy_unmanaged
- episodes/江南卖花姑娘的一天（无 lock、无治理声明） -> legacy_unmanaged

Gate adapter：verify(episode, metadata_only=False) 只对 FAIL 返回错误字符串，legacy_unmanaged 返回空列表，
所以未来接入 Gate 时不会误伤历史 Episode，也不会把「没接入治理」当成失败。

---

## 5. 本阶段不做什么

- 不修改 machine_gate / evidence_gate（当前没有 visual profile hook，本阶段也没有新增调用点）
- 不修改 frame_contract、Story Lock、story-gates.json、episode-state.json
- 不修改 Selector Rule Engine、visual_profile_selector.py
- 不修改任何已有 Episode，不自动补齐或迁移历史 profile 绑定
- 不引入评分：只输出 error code 与证据结构，不输出分数或百分比

---

## 6. 验证

    python -m pytest tests/system -q
    python -m pytest episodes/_system -q
    python -m unittest discover -s tests/system -p "test_*.py"

专项：tests/system/test_visual_profile_lock.py（19 项，覆盖 Case1..Case8）

---

## 7. 结论与后续

Phase 3.5 完成的是「校验能力」，不是「运行时接入」。当前状态：

    Profile 资产               ✅ Phase 2.2
    Registry                   ✅ Phase 2.1 / 2.2
    Selector 设计与契约         ✅ Phase 3.1 / 3.2
    Rule Engine                ✅ Phase 3.3
    Selection Integration 设计  ✅ Phase 3.4
    Selection Evidence Gate    ✅ Phase 3.5（本阶段）
    Visual Lock Runtime 接入    ⬜ Phase 4
    Gate 生产接入               ⬜ Phase 4

Phase 4 才让新建 Episode 自动走 Story Intent -> Selector -> Visual Lock -> Production；
在此之前选择证据链先冻结，避免把尚未稳定的选择逻辑直接绑进生产流程。

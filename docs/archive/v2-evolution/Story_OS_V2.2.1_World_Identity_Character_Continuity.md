# Story OS V2.2.1 — World Identity + Character Continuity Patch

## 默认行为

从 Story OS 2.2.1 开始，新 Episode 默认继承：

- 中国大陆现实语境
- 中国本地居民
- 普通 19–30 岁中国年轻人为默认主角方向
- 符合地点与年代的中国住宅/城市/乡村/商业环境
- 中国道路、车辆、日常消费品语境
- 不默认引入外国人物、外国建筑或外国文化道具

这里锁定的是 **national/cultural context**，不是强制汉族外貌。
中国内部保持自然地域与民族多样性，只有 Story 明确指定时才进一步收窄。

## Episode Override

默认无需创建 `meta/world-identity.json`。

如果故事明确发生在其他国家/文化环境，可以使用：

```bat
python -X utf8 scripts/story_world_identity.py set-override "<episode>" ^
  --country Japan ^
  --region Japan ^
  --culture-context contemporary_japanese_daily_life ^
  --language-context Japanese ^
  --architecture-context location-appropriate_Japanese_built_environment ^
  --nationality-context Japanese ^
  --resident-context Japanese_local_residents ^
  --protagonist-identity "ordinary Japanese young adult"
```

之后该 Episode 将完全按 override 生产。

## 人物连续性

新增派生合同：

`meta/runtime/contracts/character-appearance-anchor.json`

它从：

- Character Contract
- Character Visual Contract
- World Identity effective contract

编译出稳定人物锚点。

它不取代 Visual Lock Pixel Master。
关系是：

```text
Character Contract
        +
Character Visual Contract
        +
World Identity
        ↓
Character Appearance Anchor（文字/结构锚点）
        ↓
Resolved Frame Contract
        ↓
Visual Lock ordinary baseline
        ↓
Pixel Master（更强的像素身份锚点）
```

## 像素 Review 新增

仅对 `tool_version >= 2.2.1`：

- `world_identity_fidelity`
- `character_appearance_anchor_fidelity`
- `cultural_environment_fidelity`

Issue Codes：

- `WORLD_IDENTITY_DRIFT`
- `CHARACTER_APPEARANCE_DRIFT`
- `CULTURAL_CONTEXT_DRIFT`

旧 2.2.0 与更早 Episode 不受影响。

## 生产前 Checklist

```bat
python -X utf8 scripts/story_v221_readiness.py "<episode>" --stage preimage
python -X utf8 scripts/story_v221_readiness.py "<episode>" --stage production
```

Production 模式还会验证 Resolved Frame Contract 真的包含：

- World Identity
- Character Appearance Anchor
- 两者 SHA
- Production Prompt block

## Codex 执行速度

新增：

`config/index.yaml`（旧 `.storyos/runtime-index.json` 已归档到 `.storyos/history/legacy/`）

Scoped Codex Worker 会把对应 stage 的快速读取索引直接嵌进 bounded prompt：

- 默认禁止递归扫描仓库
- 优先只读 Execution Capsule + stage read set
- 只有缺依赖/冲突时才扩大读取

这解决的是 Pilot 中大量时间花在“反复定位源码/规范”的问题。
它只能降低无效扫描成本，不承诺固定墙钟时间。

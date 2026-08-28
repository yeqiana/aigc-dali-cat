# dali-cat-story adapter scripts — V2.0.3

本目录只保存 **thin adapter wrappers / helpers**，不是第二套 Story OS engine。

## 本目录真实文件

| Script | Purpose |
|---|---|
| `bootstrap_episode.py` | compatibility wrapper；转发到 `episodes/_system/episode_state.py init` |
| `hash_asset.py` | 轻量 SHA-256 helper；不管理 stage |
| `validate_all.py` | compatibility wrapper；转发到 `episodes/_system/validate_episode.py` |

## Canonical Engine 在哪里

以下能力全部只存在于 `episodes/_system/`：

- `episodes/_system/episode_state.py`
- `episodes/_system/validate_episode.py`
- `episodes/_system/machine_gate.py`
- `episodes/_system/evidence_gate.py`
- `episodes/_system/canvas_normalize.py`
- `episodes/_system/delegated_delivery.py`
- `episodes/_system/codex_auto_orchestrator.py`
- `episodes/_system/contract_sync.py`

不要为了让 Skill “看起来完整”而复制这些实现。Skill 通过 wrapper 或直接调用 canonical path 使用它们。

## Contract self-check

```bash
python episodes/_system/contract_sync.py
python episodes/_system/test_v203_contract_hardening.py -v
```

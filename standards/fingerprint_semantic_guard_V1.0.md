# Fingerprint Semantic Guard V1.0

> Story OS V2.0.3.6 active subordinate. 只补 Recent-5 语义去同质化证据，不增加 stage，不替代 `meta/episode-state.json`。

## 目标

V2.0.3.5.x 的 deterministic fingerprint 只在维度文本完全一致时计分，因此同一套路只要换一套措辞就可能绕过 Recent-5。

V2.0.3.6 使用双层判定：

1. exact-string deterministic score；
2. fresh isolated semantic-equivalence critic。

最终分数固定为 `effective_similarity = max(exact_similarity, semantic_similarity)`。
最终 mechanism veto 固定为 `exact_veto OR semantic_veto`。

critic 只输出九个维度是否“底层功能/机制相同”的布尔值，不得自行打分。权重和 veto 始终由 Python 计算。

## 证据

V2.0.3.6 新篇必须生成：
- `meta/recent5-semantic-review.json`
- `meta/recent5-semantic-critic.jsonl`
- `meta/recent5-review.json` schema 2

semantic review 必须绑定当前 fingerprint SHA、registry SHA、实际 Recent-5 episode IDs、fresh CODEX_ISOLATED provenance，以及 critic log SHA256。

任何 fingerprint、registry、历史集合或 critic log 漂移，都必须重新审。

## Skin-swap veto

如果 `core_anomaly_mechanism + middle_escalation + climax_form` 三个维度语义上同时等价，Python 直接 veto。

## 兼容

V2.0.3.5.1 及更早 episode 保持原证据合同。只有 contract version >= 2.0.3.6 的新篇强制本门禁。

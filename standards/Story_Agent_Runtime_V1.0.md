# Story Agent Runtime V1.0

Story Agent Runtime 是 Story OS 的执行控制层，负责 Request Normalization、Intent Resolution、Route Decision、Runtime Trace。

它不负责创作权威，不替代 Story / Storyboard / Frame Contract，不创建第二 Episode Stage。

唯一状态源仍是：
`<episode>/meta/episode-state.json`

以下均为 Evidence / Derived Runtime Data：
- `meta/runtime-route.json`
- `meta/runtime/trace-events.jsonl`
- `meta/runtime/trace-summary.json`
- `meta/provider-receipts/*.json`

执行链：
`Raw Request → Normalize → Intent Resolve → Runtime Request → Route Decision → Workflow DAG`

默认确定性规则优先，LLM Request Rewrite 不是默认路径。

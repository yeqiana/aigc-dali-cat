# Story OS Phase 3 — First-Pass Review Aggregation + ONE Repair Wave

## Current repair flow audit

- Generated candidates enter the Production Queue and are reviewed asynchronously by the Phase 2 review lane.
- Before Phase 3, Fast Scout batch findings could authorize `scout_repair`, and `REPAIR_FAILED_IMAGES` materialized them frame by frame before the full Production semantic review.
- `REVIEW_FINAL_PRODUCTION` runs the full candidate-set semantic review. The ledger records `CONTENT_FAILED` / `REPAIR_AUTHORIZED`; `content_repairs_used` is charged when the repair generation begins.
- Repair prompts were previously composed locally in `auto_repair_enqueue.py`, then scheduled through `image_scheduler.py`.
- Repair generation results return through the existing review queue and final semantic review. A failed repair candidate becomes `NEEDS_USER` in the Production Ledger.
- Visual Lock baseline/calibration and explicit user/authority-refresh continuations retain separate existing paths. They do not share the automatic Production content-repair wave policy.
- The Generation Attempt Authority and Phase 2 Review Queue remain independent authorities; this phase changes neither.

## Current Generation / Review flow snapshot

- Generated artifact: committed by the existing image scheduler into its durable production queue and projected into the Production Ledger.
- Review trigger: artifact completion enqueues the Phase 2 durable Review Work Item; Fast Scout consumes it on the independent Review Lane. Full candidate-set semantic review remains the formal Production content decision.
- Pre-Phase 3 serialization point: Fast Scout `scout_repair` could feed `REPAIR_FAILED_IMAGES` before the complete semantic review. That Production path is now deferred to the barrier.
- Current configured concurrency: Generation `production.max_inflight_images = 5`; Review `production.review.max_inflight = 2`. Phase 3 leaves both unchanged.
- Pending Review and its claim/receipt are persisted in the existing scheduler queue's review work items. Restart releases expired/running claims and reuses a matching generation-key + artifact-SHA + policy-SHA receipt.
- Repair trigger: the first full Production semantic review now materializes the aggregate repair plan; Visual Lock and explicit authority/user exceptions keep their existing entry points.
- Circuit breaker: `runtime_circuit_breaker.py` continues to count repeated technical/execution failures and apply its existing cooldown/hard-stop codes. It does not own queue backpressure or repair-wave eligibility.
- Reused components: existing full-frame semantic evidence, Episode-bound `prompt.repair` Model Policy, Scoped Codex receipts, image scheduler, Phase 1 Attempt Authority/Gateway, and Phase 2 Review Queue.
- Minimal Phase 3 surface: defer only Production scout/immediate repair admission, add one aggregate plan and scoped prompt task, then resume the existing scheduler/review path. No DAG node, database table, second scheduler, or Attempt Authority changes.

## Phase 3 behavior

1. The full-frame semantic candidate evidence is the First-Pass barrier. No automatic Production content repair can materialize before it is complete.
2. Fast Scout remains useful for early evidence, but cannot authorize a Production repair or dispatch one.
3. `repair_aggregator.py` binds one deterministic plan to the full-review evidence SHA, current artifact SHA, source generation key, logical asset identity and Episode-bound `prompt.repair` policy SHA.
4. Eligible prompt tasks execute as an internal Scoped Codex Task with role `prompt.repair`; this does not add a top-level Runtime DAG node. The task fingerprint and Model Execution Receipt support resume and receipt reuse.
5. The persisted `meta/runtime/repair-wave-1.json` is the canonical single automatic Production repair plan. Partial materialization reuses its plan and queue identities. New evidence cannot open Wave 2.
6. Each repair is queued through the existing `image_scheduler.py`, so Attempt reserve and real Provider dispatch continue through the Phase 1 MySQL Authority and Image Generation Gateway.
7. Repair output receives the existing Phase 2 Review Lane and full semantic review. A second content failure closes as `NEEDS_USER`; it cannot schedule another automatic content wave.

## Eligibility

A finding is eligible only when the full-review artifact SHA still matches the current candidate, a source generation key and content failure code exist, the Episode-bound Attempt Authority reports at least one remaining attempt, the frame is not human-only, and the Ledger has authorized the first content repair. Budget-exhausted and stale findings are excluded; human-only findings go to `NEEDS_USER`.

Technical retry remains separate from content repair. Pre-dispatch technical failures do not create a repair wave. Provider generation still obeys the existing hard cap of two real attempts per logical asset.

## Verification boundary

Contract tests use synthetic evidence, stubbed prompt execution and queue items. No real image generation is performed. Phase 3 does not implement Incremental Verify or broader continuity invalidation. Production mode remains `COLLABORATIVE`.

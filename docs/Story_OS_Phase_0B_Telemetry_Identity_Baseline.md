# StoryOS Phase 0B — Telemetry / Identity / Baseline

## Scope

Phase 0B adds observation to the existing Runtime. Telemetry is fail-soft and cannot select work, models, providers, retries, stage transitions, gates, or release state. `WORKER_DISPATCH_COMMITTED` is descriptive evidence only; it does not grant or consume an image attempt.

The event channel is the existing Episode-local `meta/runtime/trace-events.jsonl`, written through `runtime_observability.append_trace_event`. It is not a second event bus or authority store. Existing `episode_meta_store`, Episode performance summaries, Provider receipts, queue and lifecycle records remain their current authorities.

## Identity and event contract

Frame identity is the repository Episode namespace plus `/frame-NN` (for example `00_独立篇/04_未交的答卷/frame-03`); it is independent of candidate paths, temporary filenames, queue filenames, provider request IDs, and database availability. Non-frame assets use stable segments, for example `00_独立篇/04_未交的答卷/visual-lock/P01`.

Runtime events share a normalized envelope with a timestamp, event ID, Episode/run/trace identity, step and type, optional logical asset/frame, model policy binding, provider/runner/worker, attempt/generation reference, queue values, durations, status and evidence reference. Inapplicable values are null. Controller model/effort and payload model/quality are separate fields.

`safe_record_runtime_event()` is the write boundary for best-effort instrumentation. It catches telemetry failures and returns `False`; production behavior must not depend on that return value.

Each real Scoped Codex model call also writes one `MODEL_EXECUTION` trace event and an immutable per-call evidence file under `meta/provider-receipts/model-executions/`. The receipt references the Episode-bound Model Policy SHA and records the CLI-bound model/effort. When the JSONL stream does not report a confirmed model, `effective_model_source` is `EXPLICIT_RUNTIME_BINDING`; it must not be described as Provider-confirmed.

## Timing interpretation

- `generation_total`: request to successful artifact event when both timestamps exist.
- `generation_queue_wait`: recorded wait from queued timestamp to dispatch commit.
- `observed_generation_wall`: scheduler dispatch to result received. This is not claimed as provider-internal time.
- `provider_wall`: null unless the provider supplies a measured boundary.
- `review_queue_wait`: enqueued to started; `review_execution_wall`: started to finished. Host review without a start receipt stays incomplete.
- `repair`: separate enqueue/start/finish events; no repair count or scheduling rule is changed.
- Episode elapsed, pipeline-controlled, external user wait and uncontrolled idle are distinct report fields. Missing evidence remains null.

Queue measurements are observations only. This phase adds no throttle, high-watermark action, pause, lane, lease, or attempt accounting behavior.

## Report and replay

`episodes/_system/production_timing_baseline.py <episode> --output <path>` creates a JSON baseline from observed trace events. Add `--historical-replay` to mark the source `HISTORICAL_REPLAY`, or `--source INSTRUMENTED_CANARY` for a bounded Canary report with `complete_for_observed_scope` coverage. Existing image-attempt and performance-ledger fields may be summarized as historical evidence, never promoted to instrumented runtime events. The report labels coverage partial when required event boundaries are absent and does not infer timestamps from file mtimes. Per-call model walls are counted once by `call_id` even when matching worker/review lifecycle events also carry a duration.

The historical replay for `00-04/未交的答卷` is read-only. It must not invoke an Episode command, provider, reviewer, image backend, or mutate Episode assets.

## Verification boundary

Contract tests cover stable asset keys, schema normalization, controller/payload separation, queue/execution timing arithmetic, three clocks, partial historical coverage, bound-policy immutability, per-call Receipt requirements, resume identity, generation/repair event ordering, fail-soft behavior and a 1,000-event serialization/write/aggregation timing sample. The Phase 0B instrumented Canary used three real read-only `codex exec` calls (prompt, image-input vision, orchestration) against an Episode-bound Policy; it generated no image. Its temporary Episode, trace and receipts remain local under `.codex_tmp/`.

The 2026-09-30 Canary observed 29 events, one logical asset and `complete_for_observed_scope` coverage. Review queue wait was 2 ms; Review wall was 31,188 ms. Model walls came from each real execution receipt. Historical replay for `00-04/未交的答卷` remains `partial`, with zero events. Provider image-generation E2E and live repair timing remain `DEFERRED_TO_PRODUCTION_CANARY`; their schema/order/aggregation are contract-tested and they are not Phase 0B blockers.

## Phase 0B acceptance

- `PHASE_0B_PASS`: 3 real Luna execution receipts; all contain non-empty bound Policy SHA and `effective_model_source=EXPLICIT_RUNTIME_BINDING`. Actual argv evidence records `-m gpt-6-luna`; effort is high/high/medium, and the vision call included `--image` for an existing repository image.
- Canary baseline: 29 events, 1 logical asset, 82,483 ms elapsed, 81,933 ms pipeline-controlled; Review queue wait 2 ms / execution wall 31,188 ms. No image was generated.
- `00-04/未交的答卷`: historical `partial`, event count 0; no historical Receipt or timestamp backfill.
- Model/Review/DAG/Scheduler/Repair/P4 related tests: 209 passed, 9 subtests passed. The 1,000-event sample measured 9.548 ms serialization, 813.008 ms write and 66.060 ms aggregation.
- `tests/system/test_report_regressions.py` and `unused/meta/episode-performance-ledger.json` were excluded due to concurrent modification. `git diff --check` passed.
- `production.mode=COLLABORATIVE`. Real image-generation E2E and live repair E2E are deferred. Phase 1 is not started.

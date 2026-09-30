# StoryOS Phase 1 — Unified Generation Attempt Authority

## Scope and result

Phase 1 closes the authority boundary for real image generation. It does not
start the Generation/Review dual lane. The hard per-Logical-Asset limit is a
code constant (`MAX_REAL_IMAGE_GENERATION_ATTEMPTS_PER_ASSET = 2`); Episode and
user authorizations cannot raise it. A single in-flight reservation is allowed
for each asset.

No real image was generated during Phase 1 verification. Provider entrypoints
were exercised with fake callbacks and the TEST_ONLY MySQL 8.0 container.

## Current attempt authority map

| Field or module | Current meaning and persistence | Dispatch authority? | Phase 1 role |
| --- | --- | --- | --- |
| `generation_attempt_authority.py` | Atomic reserve, fencing, consumed count and attempt lifecycle in MySQL | Yes | Sole attempt allow/deny authority |
| `TB_GENERATION_ASSET_STATE` | Per-episode Logical Asset consumed count, active index and monotonic fencing counter | Yes | Durable lock/state row |
| `TB_GENERATION_ATTEMPT` | Stable generation key, lease hash/fence, lifecycle timestamps and model/provider context | Yes | Durable attempt evidence and idempotency key |
| `raw_candidate_budget.py` | Existing claim/commit/release API plus legacy evidence reads | No independent authority | Compatibility facade that delegates claims and terminal updates to MySQL |
| `meta/runtime/raw-candidate-budget.json` | Historical claims and compatibility projection | No | Conservative legacy reconciliation / diagnostics |
| `production_ledger` provider attempts | Business attempt, candidate, provider receipt and review evidence | No | Evidence only; historical invoked rows seed fail-closed reconciliation |
| `image_scheduler` item `attempts` | Scheduler retry epoch and technical retry count | No | Scheduling metadata only; never grants provider calls |
| `provider_attempt` receipt | What the legacy production ledger records about provider activity | No | Evidence only; new generation identity is `generation_key` |
| Redis | Not used by attempt authority | No | No authority role |

## Identity and state transitions

Frame assets use `logical_asset_identity.frame_asset_key`, so visual lock,
production, repair and retry share `<episode_id>/frame-<NN>`. Non-frame assets
use stable hierarchical keys. `generation_key` is a deterministic hash of
episode id and Logical Asset key plus attempt index; pre-dispatch retries reuse
the same key, while a committed dispatch permanently consumes that index.

The allowed path is:

```text
REQUESTED -> RESERVED -> WORKER_DISPATCH_COMMITTED
                         -> IMAGE_GENERATION_OBSERVED (optional)
                         -> SUCCEEDED | FAILED_AFTER_DISPATCH | OUTCOME_UNKNOWN
```

Failure before dispatch releases the reservation without consuming the slot.
Dispatch commit increments the durable consumed count in the same MySQL
transaction. Lease expiry before dispatch releases the index; expiry after
dispatch marks the result unknown and leaves the count consumed. A later lease
gets a higher fencing token, so a stale worker cannot commit.

## Provider boundary

The image generation gateway guards Codex single-image dispatch, Codex native
batch dispatch, OpenAI image API batch dispatch, and WORK/WEB host image request
dispatch. A batch reserves and commits one lease per Logical Asset atomically.
Provider recovery that reuses an existing raw file and user asset adoption do
not reserve or consume another attempt. User adoption records
`USER_ASSET_ADOPTED` evidence with `source=USER_SUPPLIED`.

## Phase 1 validation

- MySQL TEST_ONLY concurrency and lifecycle contract: real last-slot race,
  single-inflight, fencing, pre-dispatch recovery, post-dispatch consumption,
  duplicate dispatch denial, stable key, cross-scope key, gateway denial,
  legacy over-cap denial and batch atomicity.
- Compatibility facade, scheduler admission, image runtime/provider contract,
  provider recovery, production ledger and telemetry contract suites pass.
- StoryOS config validates; Python compile and `git diff --check` pass.
- `tests/system/test_report_regressions.py` remains excluded due to concurrent
  modification. `unused/meta/episode-performance-ledger.json` is likewise
  excluded and untouched.
- Schema DDL is registered in `platform/repository/mysql/schema_v2.py`; the
  deployment must apply the standard schema migration before enabling a runtime
  that dispatches images. Missing MySQL/schema fails closed.
- `production.mode` remains `COLLABORATIVE`. Real image generation telemetry
  end-to-end remains deferred to a later production canary.

## Phase boundary

Phase 1 ends at the unified attempt authority and provider dispatch guard.
Generation/Review dual lanes, review backpressure, repair-wave changes,
incremental verification and CODEX_MANAGED cutover are not part of this phase.

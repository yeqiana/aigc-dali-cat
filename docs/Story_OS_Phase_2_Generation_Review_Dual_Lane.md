# StoryOS Phase 2 — Generation / Review Dual Lane

## Current Generation / Review Flow Audit

1. Generated pixels are returned by the existing image worker and committed through `image_scheduler` or `batch_scheduler` into the production ledger and shared production queue.
2. The per-frame Fast Scout was previously called inside `image_worker_pool.execute`; batch execution called it after the generation batch, serially. Final semantic review remains a downstream Runtime DAG step after production.
3. The in-worker Fast Scout put its model-call wall time on the Generation worker critical path. Phase 0B's measured Vision review wall was about 31 seconds.
4. Generation concurrency remains `production.max_inflight_images = 5`. Review has its own conservative `production.review.max_inflight = 2`.
5. Pending queue entries and review work items are stored together through the existing `scheduler_core` / `production_queue_store` persistence boundary, following the Episode's configured backend (legacy Episode file, Runtime Workspace, or configured Redis-only mode). No new broker or storage authority is introduced.
6. On scheduler restart, stale `running` review claims are returned to `queued`; generated queue artifacts without a Review item are reconciled idempotently.
7. Fast Scout outcomes continue through the existing evidence projection and repair assessment paths. The Review Lane never calls an image provider. Formal repair scheduling remains under the existing Generation scheduler and Attempt Authority.
8. `runtime_circuit_breaker` continues to handle repeated technical/execution failures. Review queue pressure uses a separate persisted pause latch and does not open a circuit.
9. Reused components: shared production queue persistence and lock, model policy binding, `fast_frame_scout`, production ledger, `frame_scout_persistence`, runtime telemetry, and the existing batch repair assessment.
10. The serial bottleneck was Fast Scout execution in `image_worker_pool` and sequential post-batch scouting. Both paths now enqueue attempt-scoped review work and release Generation workers before Vision review completes.

## Phase 2 Contract

- The review queue item is identified by episode, canonical logical asset key, generation key, artifact SHA-256, and review kind. It also records attempt index, exact artifact path, review model role, policy SHA, and queue time.
- Duplicate enqueue is idempotent. A single persisted claim token owns execution at a time. A receipt is saved before the queue item is finalized so resume can adopt the receipt without repeating the model call.
- Review evidence for an artifact that is no longer the current candidate remains attached to its exact queue item. It cannot overwrite the current per-frame Fast Scout projection.
- The image lane remains capped by the existing image-worker configuration. Review concurrency is independent and capped at two.
- Backpressure uses HIGH=6 and LOW=2. At HIGH, the scheduler pauses refill only; already-dispatched Generation work, artifact commits, and Reviews continue. Refill resumes only after the queue reaches LOW.
- Review failures are recorded as review outcomes; they do not directly call a Provider or claim an Attempt. Any existing repair intent returns through the normal scheduler, Attempt Authority, and Image Generation Gateway.
- The Generation Attempt Authority, its MySQL tables, max-two cap, lease, fencing, and `generation_key` ownership are unchanged.

## Verification Record

The Phase 2 test suite verifies that a slow synthetic Review overlaps with later Generation, queue idempotency and claim recovery, recovery of generated artifacts missing a Review item, receipt reuse, stale artifact protection, backpressure hysteresis, and the Phase 1 Attempt Authority regression contracts.

Synthetic timing (4 items; 120 ms fake Generation; 350 ms fake Review; Review concurrency 2): serial wall 1.937 s; dual-lane wall 0.966 s; measured improvement 50.1%. These are deterministic contract timings, not production performance claims.

No real image generation is performed by the Phase 2 contract tests. Provider image generation remains unverified end-to-end and is intentionally deferred to a production canary.

Production mode remains `COLLABORATIVE`. Phase 3 is not started.

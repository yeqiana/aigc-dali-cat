# Phase 5A Provider Capability Unblock — BLOCKED

**Date:** 2026-10-01

**Mode:** `COLLABORATIVE`

**Phase 5B:** `NOT STARTED`

## Result

`PHASE_5A_PROVIDER_PATH_BLOCKED`. The two execution roles can use separate routes: the local Codex CLI route has passed the frozen `image.controller` text call `gpt-6-luna / high`, while no automated independent Pixel Provider is configured for `gpt-image-2.5-flare / high`. No new Canary, Image Attempt, or image was created in this capability check.

The dedicated Controller probe uses a regular text-only scoped call with explicit `-m gpt-6-luna` and `model_reasoning_effort="high"`; it does not enable `image_generation`. The previous fused ChatGPT Codex image-tool route rejected Luna with HTTP 400 / unsupported model. The independent OpenAI Images API route is statically registered for Flare/high, but its required API credential is absent, so this route is unavailable. The response body and all secret values are intentionally excluded.

## Candidate matrix

| Candidate | Finding | Phase 5A eligible |
|---|---|---:|
| Controller: Direct Codex CLI / `codex_user_runner` default endpoint | Exact `gpt-6-luna/high` text-only scoped probe passed with explicit CLI binding; no image tool enabled | Yes, Controller only |
| Payload: OpenAI Images API | Registry contract supports Flare/high; non-generation capability check found credential absent | No |
| Legacy fused `codex_subscription` image route | Exact Luna was rejected as unsupported on the configured ChatGPT Codex endpoint; it couples Controller and image tool execution | No |
| WORK / Workspace Provider | Model and reasoning are host-selected; exact Luna binding is not proven | No |
| Product Runtime image action | Requires a host action and returned artifact; current execution is not automated from this environment | No |

The Controller/Payload coupling has been removed from the active single-frame worker path: Luna now produces a validated canonical payload request before the independent Pixel route is checked. If the Flare API route is not configured, the worker blocks before Attempt claim. Legacy Batch dispatch is denied for split-policy episodes so it cannot silently route around the Controller or the canonical request. No candidate passed `PHASE5A_EXECUTION_PATH_READY` because the Pixel lane has no configured automated provider. The frozen Model Policy was not changed, and no fallback or model substitution was used.

## Execution topology audit

- `codex_subscription_image.invoke_codex()` builds the legacy `codex exec` argv with `--enable image_generation` and a worker prompt that requires the tool as its first action. That is why the old route made the Controller transport own the Pixel tool call; it is an implementation coupling, not an Attempt Authority requirement.
- The split path now builds the `ImagePayloadRequest` via the text-only scoped Controller in `image_payload_controller.py`. The request is fingerprinted and checked against the Episode-bound policy, contract, references, canvas, and asset identity.
- `openai_images_provider.generate_native_batch()` is an independent Pixel Provider. It calls `image_generation_gateway.provider_generate_many()`, where the durable Attempt lease/fence is committed immediately before provider handoff. The active worker checks its non-generation route configuration before claiming an Attempt.
- `WORKER_DISPATCH_COMMITTED` therefore protects Pixel dispatch, not the Luna text Controller. Controller or Payload preflight failures occur before Attempt claim; after Gateway commit, the Attempt stays consumed under the Phase 1 contract.
- The current route matrix has no eligible automatic Pixel path: OpenAI Images API lacks configured credentials, and Product Runtime requires a host action. WORK is host-selected and cannot certify exact Luna. No shim model is being used.

## Attempt and asset accounting

The prior Canary remains unchanged:

- Canary ID: `phase5a-collab-fixture-d032d38510`
- Logical asset: `_external/5b6de9e46d4ae6dc/frame-01`
- Generation key: `ga1-0fa11429747e700ae6de066daaf7a8665ae8f9df204e890c-a1`
- Attempt 1: `OUTCOME_UNKNOWN`, permanently consumed; `attempts_consumed=1`

Its status, receipt, and generation key were not rewritten or reused. Because no new candidate passed the exact-model preflight, no new Canary or Attempt was created, and no image generation was dispatched.

## Guardrails retained

- `production.mode` remains `COLLABORATIVE`.
- The formal four-admission Visual Lock gate remains unchanged.
- No Stage or Release authority was written.
- No credentials, tokens, or raw provider response content are included in this report.
- Phase 5A remains blocked pending an automated independent Pixel Provider configured for `gpt-image-2.5-flare/high`.
- Phase 5B is `NOT STARTED`.
## Login-auth Payload route convergence update

The repository now explicitly disables the API-key image route and keeps codex_subscription enabled. Provider selection remains authoritative in image_provider_runtime; a present OPENAI_API_KEY can no longer re-enable the disabled API route.

The split Production path now uses the configured provider. image_payload_transport delegates preflight to the selected provider, image_worker_pool performs provider-aware Payload preflight before claiming an image Attempt, and the Phase 5A Canary uses the same preflight. codex_subscription_image can execute a frozen ImagePayloadRequest through a login-auth transport shim. The shim is not image.controller and may only invoke image_generation once using the already frozen payload model, quality, canvas, references, and scene prompt.

The technical transport model is selected from the live login account model catalog and validated in an image-tool-enabled text probe before any image Attempt is reserved. It is not added to Episode Model Policy and cannot rewrite Luna or Flare.

Current validation:
- API-key route configured: false.
- Selected one-image route: codex_subscription.
- API key required: false.
- Config validation: PASS.
- Changed module compilation: PASS.
- Direct executable contract tests: 18 passed / 0 failed.
- Live login-auth Payload preflight: BLOCKED / LOGIN_AUTH_IMAGE_TOOL_UNAVAILABLE because the interactive codex_user_runner endpoint currently points to a stopped runner process while Codex is being installed or updated.
- The blocked preflight reports image_attempt_authority_called=false and image_generation_called=false, so no new Attempt or image was consumed.
- The historical Canary OUTCOME_UNKNOWN Attempt remains unchanged.

The remaining Phase 5A blocker is therefore the offline interactive runner, not API credentials or Controller/Payload routing. Real Provider Canary remains pending and Phase 5B remains NOT STARTED.

## 2026-10-01 Real Canary Attempt 1 update

This section supersedes the older operational blocker statements above while preserving them as historical evidence.

The login-auth route, bounded UNKNOWN-capability gate, Payload transport preflight, and exact Luna Controller preflight all passed. The replacement Canary phase5a-collab-retry-087b52d549aa then entered its first real image Attempt.

Authoritative result:

- Logical asset: _external/76251ec2bfb424e9/frame-01
- Attempt 1 generation key: ga1-c6f16e1fba3d2c7bb8955ad7314e5b24ffa16e81564ac087-a1
- Provider: codex_subscription
- Transport: gpt-5.6-sol / low
- Payload: gpt-image-2.5-flare / high
- Requested canvas: 1080x1350, aspect 4:5
- Real provider RAW: 1448x1086
- RAW SHA-256: 654acef2e272d77798471a612ea9fd19ee2534b7ca84acf91e73df18d3eb837b
- Queue result: blocked
- Technical failure: ASPECT_RATIO_MISMATCH
- Ratio delta: 0.666666667
- Attempt status: OUTCOME_UNKNOWN
- Attempts consumed: 1
- Remaining attempts: 1
- Stage authority mutation: none
- Release authority mutation: none
- Review did not start because the provider RAW failed the canonical canvas gate.

image_blocked_recovery inspect rejects deterministic local recovery with provider_crop_exception_limit_exceeded. The configured provider-crop exception limit is 0.06, so this RAW cannot be silently center-cropped or normalized into the formal 4:5 candidate.

The persisted Provider Receipt proves that StoryOS requested the correct canonical canvas. The failure is therefore downstream of the canonical request: the image tool/provider returned a 4:3 landscape RAW despite the 4:5 portrait request. The transport prompt has been hardened to state exact dimensions, exact aspect ratio, explicit PORTRAIT/LANDSCAPE orientation, and that shot-scale words such as wide shot must never change the locked canvas orientation.

No second real image dispatch was made. Attempt 2 remains unused. Under the current Phase 5A contract, Attempt 2 is reserved for a natural Review-driven REPAIR_NEEDED path, not for an automatic technical transport retry. Phase 5A therefore remains BLOCKED at the real-provider canvas compatibility boundary. Phase 5B remains NOT STARTED.

# Phase 5A Provider Capability Unblock — BLOCKED

**Date:** 2026-10-01

**Mode:** `COLLABORATIVE`

**Phase 5B:** `NOT STARTED`

## Result

`PHASE_5A_REAL_PROVIDER_BLOCKED`. No compatible execution environment has been demonstrated for the frozen `image.controller` binding `gpt-6-luna / high`. No new Canary, Image Attempt, or image was created in this capability check.

The exact-model text probe against the same configured endpoint used by the image route explicitly requested `gpt-6-luna` and `reasoning_effort=high`; it was rejected with HTTP 400 / unsupported model. The response body is intentionally not retained here. A probe against the CLI default endpoint is not evidence for the configured production endpoint and is excluded from the capability decision.

## Candidate matrix

| Candidate | Finding | Phase 5A eligible |
|---|---|---:|
| `codex_subscription` / configured image endpoint | Exact `gpt-6-luna/high` text probe rejected as unsupported | No |
| Direct Codex CLI / `codex_user_runner` default endpoint | Tiny `gpt-6-luna/high` text probe passed in about 25.5 seconds with `EXPLICIT_RUNTIME_BINDING`; this endpoint differs from the image worker's configured ChatGPT endpoint, so it does not establish capability on the production image route | No |
| WORK / Workspace Provider | Model and reasoning are host-selected; exact Luna binding is not proven | No |
| `api_http` | Required route configuration/environment is absent | No |
| Registry-declared image provider capability | Registry declares image capability, but exact-model execution and image E2E remain unconfirmed | No |

No candidate passed `PHASE5A_PROVIDER_ENV_READY`. The frozen Model Policy was not changed, and no fallback or model substitution was used.

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
- Phase 5A remains blocked pending an execution environment that proves exact `gpt-6-luna/high` capability on the same configured endpoint and auth context.
- Phase 5B is `NOT STARTED`.

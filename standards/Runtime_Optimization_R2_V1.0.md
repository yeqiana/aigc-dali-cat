# Story OS V2.1 Runtime Optimization R2

## Scope

R2 is runtime optimization only. It does not add a new Episode Stage and does not remove any formal quality gate.

### R2-A Multi-level Cache
- L0 process parsed JSON/text cache
- L1 episode SHA-bound caches (existing Execution Capsule / Frame Contract / Prompt Package)
- L2 global content-addressed resource-selection cache under `.storyos_cache/`
- L3 explicit negative-fingerprint API for safe provider/model failures only

### R2-B Shared Resource Library
Root `library/` stores reusable reference descriptors and registered reference assets.
Final episode images are never reused by default.

### R2-C Preproduction Handoff
`preproduction_only` creates Story/Storyboard/Character/Environment/Frame Contracts and writes:
`meta/preproduction-handoff.json`.

### R2-D image_continue
Codex verifies handoff SHA before continuing. Story rewrite is forbidden.
Derived caches may be rebuilt. Authority mismatch => `HANDOFF_SHA_MISMATCH`.

### R2-E Visual Lock 1+3
Existing V2.1 plan already encodes:
baseline first -> worst / first anomaly / high-impact depend on baseline.
R2 makes this the documented runtime strategy.

### R2-F Intro + Title policy
Final intro begins from one of four reference families:
1. 年份 + 行动
2. 状态 + 时机 + 出行
3. 身份 + 最近发现
4. 临近节点 + 决定

Templates are structure references, not literal variable substitution.

Title: generate exactly 1 internal candidate; not required for PUBLISH_READY and not included in delivery by default.

## Immutable Request vs mutable execution

`meta/runtime-request.json` stays immutable.

When a `preproduction_only` episode is handed to Codex, switching to `image_continue`
writes `meta/runtime-execution.json`; it never overwrites the original request.

```text
runtime-request = original user intent
runtime-execution = current continuation mode
preproduction-handoff = authority bridge
```

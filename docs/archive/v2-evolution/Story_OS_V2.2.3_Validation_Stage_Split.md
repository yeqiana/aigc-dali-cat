# Story OS V2.2.3 — Validation Stage Split

## Why

Do not force lightweight Bootstrap to create all preproduction assets just to satisfy one oversized validator.

The lifecycle is now:

```text
Story MD
  ↓
Bootstrap
  ↓
Bootstrap Validate
  ↓
Preproduction
  ↓
Preproduction Validate
  ↓
Smoke Test
  ↓
Visual Lock
  ↓
Production
```

## Developer commands

### 1. Bootstrap validation

```bat
python -X utf8 scripts/story_validate.py bootstrap "episodes/12_千寻/01_那条不存在的隧道"
```

Success:

```text
BOOTSTRAP_VALIDATE_PASS
```

Meaning:

```text
READY_FOR_PREPRODUCTION
```

This stage checks only:

- Episode Blueprint
- Chapter Lock
- Visual Profile
- Asset Manifest

It does NOT require:

- Character Master
- Location Master
- Prop Master
- Resolved Frame Contracts

---

### 2. Preproduction validation

After preproduction is complete:

```bat
python -X utf8 scripts/story_validate.py preproduction "episodes/12_千寻/01_那条不存在的隧道"
```

Success:

```text
PREPRODUCTION_VALIDATE_PASS
```

Meaning:

```text
READY_FOR_SMOKE_TEST
```

Checks include:

- Bootstrap dependency
- Character Contract
- Location / Environment Contract
- Device / Prop Contract
- Asset Manifest
- Resolved Frame Contracts
- Authority / Binding
- SHA or digest evidence
- `current_story_branch` authority scope

---

## Reports

Default output:

```text
<episode>/meta/validation/bootstrap_validation_report.json
<episode>/meta/validation/preproduction_validation_report.json
```

Disable report writes with:

```bat
--no-write-report
```

## Important

`ASSET_LOCK_MISSING`-style strict checks belong to preproduction/smoke/production gates, not the initial bootstrap gate.

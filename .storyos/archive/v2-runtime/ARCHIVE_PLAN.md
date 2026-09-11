# V2 Runtime Archive Plan

Date: 2026-09-11

## Archive Scope

The following historical runtime artifacts are approved for archive:

- `.storyos/backups/`
- `.storyos/smoke/`

## Archive Target

```
.storyos/archive/v2-runtime/
├── backups/
└── smoke/
```

## Safety Rules

- Do not delete historical evidence.
- Do not remove `.storyos/history/install/` references.
- Do not touch current V3 runtime files.
- Do not touch `episodes/_system` runtime implementations.
- Do not touch EP003 production assets.

## Status

Completed: 2026-09-11.

- `.storyos/backups/` -> `.storyos/archive/v2-runtime/backups/` (73 files)
- `.storyos/smoke/` -> `.storyos/archive/v2-runtime/smoke/` (1 file)

Migration note: both source paths were gitignored and untracked, so `git mv`
was not applicable and no git history existed for them; the move was a
filesystem rename on the same volume. Per-file SHA-256 was verified identical
before and after. The new archive paths remain gitignored so historical
artifacts stay out of the tracked tree.

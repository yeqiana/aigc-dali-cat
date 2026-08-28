# dali-cat-story V1.1

This skill is an execution adapter for the repository's existing Story OS.

Authority:
1. `standards/制作规范_正式版.md` — creative authority.
2. `meta/episode-state.json` — single machine stage source.
3. `meta/release-manifest.json` — release facts.
4. `meta/story-gates.json` — gate evidence only, never a stage source.

Do not create or advance an `episode.yaml` stage.

For state changes use:

```bash
python episodes/_system/episode_state.py transition <episode_dir> <TARGET> --note "..."
```

For validation use:

```bash
python episodes/_system/validate_episode.py <episode_dir>
```

For legacy episode migration use:

```bash
python episodes/_system/episode_state.py migrate-gates <episode_dir>
```

Keep the minimal-edit contract:
- subtitle-only means base images are locked by SHA-256;
- unmentioned approved frames must not be regenerated;
- visual calibration must pass before batch production.

<!-- STORY_OS_V1_8_ADAPTER_BEGIN -->
## Story OS V1.8 adapter additions

When the user does not explicitly specify another visual style, resolve the default profile to:
`M00 / MP4 × 网吧 × 流水席旧数码质感校准版`.

Do not fake obsolete capture artifacts on a modern device. Capture physics and story era override mother-style texture.
Before STORYBOARD_LOCKED / VISUAL_CALIBRATED / PUBLISH_READY, respect V1.8 approval/text/release hash gates.
<!-- STORY_OS_V1_8_ADAPTER_END -->

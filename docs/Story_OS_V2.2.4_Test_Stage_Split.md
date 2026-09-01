# Story OS V2.2.4 Test Stage Split

## New lifecycle

Story MD → Bootstrap → Bootstrap Validate → **Visual Test (1 image)** → Preproduction → Preproduction Validate → **Production Smoke Test (1 image)** → Visual Lock 1+3 → Production.

### Visual Test
Does not require full preproduction. It only requires `BOOTSTRAP_VALIDATE_PASS`, a consistent locked Visual Profile, and one test scene.

```bat
python -X utf8 scripts/story_test.py visual "episodes/12_千寻/01_那条不存在的隧道" --scene "1990年代日本乡间，搬家车停在废弃隧道入口，千寻一家站在隧道外，真实35mm真人电影质感" --image-model gpt-image-2 --strict-model
```

Plan only:

```bat
python -X utf8 scripts/story_test.py visual "<episode>" --scene "..." --plan-only
```

The generated image is always `NON_AUTHORITY_TEST_ONLY` and cannot be promoted to a master or production frame.

### Production Smoke Test
Requires `PREPRODUCTION_VALIDATE_PASS` and uses the real `generate-for-frame` production route.

```bat
python -X utf8 scripts/story_test.py production-smoke "<episode>" --frame 01 --prompt-file "<episode>/prompts/production/01.txt" --image-model gpt-image-2
```

### Visual Authority
V2.2.4 adds `visual_profile_bridge_v224.py`. The formal Codex image backend is patched to compile Visual Profile through this bridge.

Priority:
1. explicit Episode `meta/visual-profile.json`
2. explicit `meta/story-gates.json` override, if it agrees
3. existing default M00

A mismatch stops generation with `VISUAL_PROFILE_AUTHORITY_MISMATCH`.

Blueprint drift check:

```bat
python -X utf8 scripts/story_visual_authority.py check "<episode>"
```

Safe sync (backs up the Blueprint first):

```bat
python -X utf8 scripts/story_visual_authority.py sync-blueprint "<episode>"
```

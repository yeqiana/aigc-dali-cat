#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then echo "usage: $0 /path/to/aigc-dali-cat"; exit 2; fi
PACK_ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$1" && pwd)"
[[ -f "$REPO/standards/制作规范_正式版.md" ]] || { echo "not story repo: missing canonical standard"; exit 1; }
[[ -d "$REPO/episodes" ]] || { echo "not current story repo: missing episodes/"; exit 1; }
cp -f "$PACK_ROOT/SKILL.md" "$REPO/SKILL.md"
cp -rf "$PACK_ROOT/skills" "$REPO/"
cp -rf "$PACK_ROOT/.agents" "$REPO/"
mkdir -p "$REPO/.codex/skills" "$REPO/.github/workflows" "$REPO/standards/templates"
cp -rf "$PACK_ROOT/.codex/skills/dali-cat-story" "$REPO/.codex/skills/"
cp -f "$PACK_ROOT/.github/workflows/story-gates.yml" "$REPO/.github/workflows/story-gates.yml"
cp -f "$PACK_ROOT/standards/templates/episode.template.yaml" "$REPO/standards/templates/episode.template.yaml"
cp -f "$PACK_ROOT/standards/templates/subtitles.template.yaml" "$REPO/standards/templates/subtitles.template.yaml"
cp -f "$PACK_ROOT/README_UPGRADE.md" "$REPO/README_UPGRADE.md"
echo "Done. Next: python -m pip install -r skills/dali-cat-story/requirements.txt"

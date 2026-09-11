#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archive Relocation Manifest: keep relocated Episodes verifiable.

The EP003 Production Exposure Audit exposed an archive-governance gap. When an
Episode directory is physically moved into episodes/_archive/, every frozen
evidence file that stores repository-relative artifact paths keeps pointing at
the pre-move location. The bytes survive, but paths such as
meta/release-manifest.json :: artifacts.story can no longer be resolved, so
Story Lock / Visual Lock / reference / production evidence stops being
verifiable.

This module is the additive, evidence-first repair. It does not touch the
Runtime, the production flow, the machine gate, or the archived Episode's own
frozen records. It:

  1. records the move as a first-class fact in an append-only registry
     (episodes/_archive/relocations.json): the from -> to directories plus a
     path prefix map;
  2. resolves a recorded repository-relative path through that prefix map, so an
     old path can be mapped to where the artifact lives now;
  3. verifies the declared integrity anchors (Story Lock, storyboard, visual
     spec, captions, production review and the core evidence files) by
     re-hashing them and cross-checking the pre-move hash manifest written at
     archive time.

Nothing here scores anything and nothing rewrites history: a relocation entry
proves a move happened and that the moved bytes still match the hash recorded
before the move.

The reference scan is advisory by design. Frozen evidence also contains free
prose and runtime temp references, so unresolved tokens are reported, never
treated as a hard failure on their own. Only the declared anchors fail closed.

CLI:

    python episodes/_system/archive_relocation.py list
    python episodes/_system/archive_relocation.py build <episode_dir> [--write]
    python episodes/_system/archive_relocation.py show <episode_dir>
    python episodes/_system/archive_relocation.py resolve <repo-relative-path>
    python episodes/_system/archive_relocation.py scan <episode_dir>
    python episodes/_system/archive_relocation.py verify [<episode_dir> | --all]
    python episodes/_system/archive_relocation.py self-test
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import story_json

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_REL = Path("episodes/_archive")
REGISTRY_REL = ARCHIVE_REL / "relocations.json"
MARKER_NAME = ".storyos-non-episode.json"
SCHEMA_VERSION = 1
REGISTRY_PURPOSE = (
    "Archive relocation registry: records physical moves of Episodes so frozen "
    "evidence paths stay resolvable and hash-verifiable. One entry per archived "
    "Episode keyed by current directory; rebuilding the same Episode replaces "
    "its own entry only."
)
# Frozen evidence files that carry repository-relative artifact paths.
EVIDENCE_RELS = (
    "meta/release-manifest.json",
    "meta/story-gates.json",
    "meta/production-ledger.json",
    "meta/visual-final-freeze.json",
    "meta/final-candidate-snapshot.json",
)
# release-manifest.artifacts roles promoted to strict integrity anchors.
ANCHOR_ROLES = ("story", "storyboard", "visual_spec", "captions", "production_review")
# A reference token ends at ASCII whitespace/punctuation or CJK prose
# punctuation, so a path glued to full-width Chinese text clips cleanly.
# A trailing ASCII period is prose punctuation too, but a period inside a
# path (".json") must survive, so it is only trimmed from the tail.
REF_STOP_CHARS = " \t()[]{}<>,;:，。、；：（）【】「」“”’『』《》" + chr(34) + chr(39) + chr(96)
REF_TRAIL_CHARS = REF_STOP_CHARS + "."
REF_TOKEN = re.compile(r"episodes/\S+")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path, default=None):
    return story_json.read_json(path, default=default, require_object=False)


def write_json(path, data) -> None:
    story_json.write_json(path, data)


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_rel(path, root=None) -> str:
    base = Path(root or ROOT).resolve()
    return Path(path).resolve().relative_to(base).as_posix()


def normalize_ref(raw):
    """Return the repository-relative candidate path inside an arbitrary string."""
    if not isinstance(raw, str) or "episodes/" not in raw:
        return None
    match = REF_TOKEN.search(raw)
    if not match:
        return None
    token = match.group(0)
    for index, char in enumerate(token):
        if char in REF_STOP_CHARS:
            token = token[:index]
            break
    return token.rstrip(REF_TRAIL_CHARS) or None


def registry(root=None) -> list:
    data = read_json(Path(root or ROOT) / REGISTRY_REL, default={})
    rows = data.get("relocations") if isinstance(data, dict) else None
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _prefix_items(entry):
    items = (entry or {}).get("prefix_map") if isinstance(entry, dict) else None
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def apply_prefix_map(ref, entry):
    """Map a repository-relative path from its pre-move prefix to the new one."""
    if not ref or not isinstance(entry, dict):
        return None
    for item in _prefix_items(entry):
        src = str(item.get("from") or "").strip()
        dst = str(item.get("to") or "").strip()
        if not src or not dst:
            continue
        src_dir = src.rstrip("/")
        if ref == src_dir or ref.startswith(src_dir + "/"):
            tail = ref[len(src_dir):].lstrip("/")
            dst_dir = dst.rstrip("/")
            return dst_dir + ("/" + tail if tail else "")
    return None


def resolve_ref(root, raw, entry=None) -> dict:
    """Resolve one recorded reference to a path that exists now.

    status is one of not_repo_path / direct / relocated / unresolved. Direct
    wins over relocation so an in-place sibling episode keeps resolving.
    """
    base = Path(root or ROOT)
    ref = normalize_ref(raw)
    if not ref:
        return {"input": raw, "ref": None, "path": None, "status": "not_repo_path", "relocated": False}
    if (base / ref).exists():
        return {"input": raw, "ref": ref, "path": ref, "status": "direct", "relocated": False}
    mapped = apply_prefix_map(ref, entry)
    if mapped and (base / mapped).exists():
        return {"input": raw, "ref": ref, "path": mapped, "status": "relocated", "relocated": True}
    return {"input": raw, "ref": ref, "path": mapped or ref, "status": "unresolved", "relocated": bool(mapped)}


def entry_for(root, episode_dir):
    target = str(repo_rel(Path(episode_dir).resolve(), root)).rstrip("/")
    for entry in registry(root):
        if str(entry.get("to") or "").rstrip("/") == target:
            return entry
    return None


def entry_for_ref(root, ref):
    for entry in registry(root):
        if apply_prefix_map(ref, entry):
            return entry
    return None


def marker_for(episode_dir):
    for candidate in (Path(episode_dir) / MARKER_NAME, Path(episode_dir).parent / MARKER_NAME):
        data = read_json(candidate, default=None)
        if isinstance(data, dict):
            return candidate, data
    return None, {}


def file_manifest_hashes(root, entry) -> dict:
    """Parse the pre-move archive hash manifest into {episode-relative path: sha}."""
    raw = (entry or {}).get("file_manifest") if isinstance(entry, dict) else None
    if not isinstance(raw, str) or not raw.strip():
        return {}
    path = Path(root or ROOT) / raw
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) != 3:
            continue
        digest, _size, name = parts
        out[name.strip()] = digest.lower()
    return out


def _iter_strings(obj):
    if isinstance(obj, dict):
        for value in obj.values():
            yield from _iter_strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _iter_strings(value)
    elif isinstance(obj, str):
        yield obj


def scan_references(root, episode_dir, entry=None) -> dict:
    """Advisory walk of every JSON evidence file for repository-relative paths."""
    base = Path(root or ROOT)
    counts = {"total": 0, "direct": 0, "relocated": 0, "unresolved": 0}
    samples = []
    files = 0
    for path in sorted(Path(episode_dir).rglob("*.json")):
        if "__pycache__" in path.parts:
            continue
        data = read_json(path, default=None)
        if data is None:
            continue
        files += 1
        for raw in _iter_strings(data):
            if "episodes/" not in raw:
                continue
            result = resolve_ref(base, raw, entry)
            if result["status"] == "not_repo_path":
                continue
            counts["total"] += 1
            counts[result["status"]] += 1
            if result["status"] == "unresolved" and len(samples) < 20:
                samples.append({"file": repo_rel(path, base), "ref": result["ref"]})
    return {"files": files, "counts": counts, "unresolved_samples": samples}


def _anchor_row(root, episode_dir, name, source, recorded, entry) -> dict:
    resolved = resolve_ref(root, recorded, entry)
    row = {
        "name": name,
        "source": source,
        "recorded_path": recorded,
        "resolved_path": resolved["path"],
        "status": resolved["status"],
    }
    target = (Path(root or ROOT) / resolved["path"]) if resolved["path"] else None
    if target is not None and target.is_file():
        row["sha256"] = sha256_file(target)
        row["bytes"] = target.stat().st_size
    return row


def anchors(root, episode_dir, entry=None) -> list:
    base = Path(root or ROOT)
    ep = Path(episode_dir).resolve()
    release = read_json(ep / "meta/release-manifest.json", default={}) or {}
    artifacts = release.get("artifacts") if isinstance(release.get("artifacts"), dict) else {}
    rows = []
    for role in ANCHOR_ROLES:
        recorded = artifacts.get(role)
        if isinstance(recorded, str) and recorded.strip():
            rows.append(_anchor_row(base, ep, role, "release-manifest.artifacts." + role, recorded, entry))
    for rel in EVIDENCE_RELS:
        if (ep / rel).is_file():
            rows.append(_anchor_row(base, ep, Path(rel).name, "episode-relative:" + rel, repo_rel(ep / rel, base), entry))
    return rows


def build_entry(root, episode_dir, *, written_at=None) -> dict:
    """Derive the relocation entry for one archived Episode from its own evidence."""
    base = Path(root or ROOT)
    ep = Path(episode_dir).resolve()
    _marker_path, marker = marker_for(ep)
    archived_from = marker.get("archived_from") if isinstance(marker, dict) else None
    release = read_json(ep / "meta/release-manifest.json", default={}) or {}
    episode = release.get("episode") if isinstance(release.get("episode"), dict) else {}
    to_rel = repo_rel(ep, base)
    prefix_map = []
    if isinstance(archived_from, str) and archived_from.strip():
        prefix_map.append({"from": archived_from.strip().rstrip("/") + "/", "to": to_rel + "/"})
    staging = {"prefix_map": prefix_map}
    return {
        "schema_version": SCHEMA_VERSION,
        "episode_id": episode.get("id"),
        "series": episode.get("series"),
        "title": episode.get("title"),
        "kind": marker.get("kind") if isinstance(marker, dict) else None,
        "reason": marker.get("reason") if isinstance(marker, dict) else None,
        "archived_at": (marker.get("archived_at") if isinstance(marker, dict) else None) or written_at or now(),
        "relocated_at": written_at or now(),
        "from": archived_from,
        "to": to_rel,
        "evidence_state": "frozen",
        "file_manifest": marker.get("manifest") if isinstance(marker, dict) else None,
        "prefix_map": prefix_map,
        "anchors": anchors(base, ep, staging),
        "reference_health": scan_references(base, ep, staging)["counts"],
    }


def upsert_entry(root, entry) -> dict:
    base = Path(root or ROOT)
    path = base / REGISTRY_REL
    data = read_json(path, default=None)
    if not isinstance(data, dict):
        data = {"schema_version": SCHEMA_VERSION, "purpose": REGISTRY_PURPOSE}
    rows = data.get("relocations")
    if not isinstance(rows, list):
        rows = []
    rows = [row for row in rows if isinstance(row, dict)]
    target = str(entry.get("to") or "")
    for index, existing in enumerate(rows):
        if str(existing.get("to") or "") == target:
            rows[index] = entry
            break
    else:
        rows.append(entry)
    data["schema_version"] = SCHEMA_VERSION
    data.setdefault("purpose", REGISTRY_PURPOSE)
    data["relocations"] = rows
    write_json(path, data)
    return data


def verify(root, entry) -> list:
    """Return (code, message) findings proving the relocated Episode still resolves."""
    base = Path(root or ROOT)
    if not isinstance(entry, dict):
        return [("relocation_entry_invalid", "relocation entry is not an object")]
    findings = []
    if entry.get("schema_version") != SCHEMA_VERSION:
        findings.append(("relocation_schema_unsupported", "schema_version " + repr(entry.get("schema_version"))))
    to_rel = str(entry.get("to") or "")
    target_dir = (base / to_rel) if to_rel else None
    if target_dir is None or not target_dir.is_dir():
        findings.append(("archive_dir_missing", "relocation target missing: " + (to_rel or "<none>")))
        return findings
    prefix = _prefix_items(entry)
    if not prefix:
        findings.append(("relocation_prefix_missing", "relocation entry has no prefix_map"))
    from_rel = str(entry.get("from") or "").rstrip("/")
    for item in prefix:
        if str(item.get("from") or "").rstrip("/") != from_rel:
            findings.append(("prefix_map_mismatch",
                             "prefix_map.from " + repr(item.get("from")) + " != entry.from " + repr(entry.get("from"))))
        if str(item.get("to") or "").rstrip("/") != to_rel.rstrip("/"):
            findings.append(("prefix_map_mismatch",
                             "prefix_map.to " + repr(item.get("to")) + " != entry.to " + repr(entry.get("to"))))
    manifest = file_manifest_hashes(base, entry)
    for anchor in entry.get("anchors") or []:
        if not isinstance(anchor, dict):
            continue
        name = str(anchor.get("name") or "?")
        recorded = anchor.get("recorded_path")
        resolved = resolve_ref(base, recorded, entry)
        if resolved["status"] == "unresolved" or not (base / str(resolved["path"] or "")).is_file():
            findings.append(("anchor_unresolved", name + ": " + str(recorded)))
            continue
        path = base / resolved["path"]
        actual = sha256_file(path)
        expected = str(anchor.get("sha256") or "").lower()
        if expected and actual != expected:
            findings.append(("anchor_hash_drift", name + ": " + actual[:12] + " != recorded " + expected[:12]))
        try:
            rel_in_ep = path.resolve().relative_to(target_dir.resolve()).as_posix()
        except ValueError:
            rel_in_ep = None
        want = manifest.get(rel_in_ep) if rel_in_ep else None
        if want and want != actual:
            findings.append(("file_manifest_hash_mismatch",
                             name + ": " + actual[:12] + " != archive manifest " + want[:12]))
    return findings


def self_test() -> None:
    import tempfile
    with tempfile.TemporaryDirectory(prefix="archive relocation self test ") as td:
        base = Path(td)
        archive = base / "episodes/_archive"
        ep = archive / "20260911_EP099_abandoned_demo"
        (ep / "meta").mkdir(parents=True)
        (ep / "docs").mkdir(parents=True)
        story = ep / "docs/story.md"
        story.write_text("story lock\n", encoding="utf-8")
        write_json(ep / "meta/release-manifest.json",
                   {"artifacts": {"story": "episodes/10_demo/03_demo/docs/story.md"}})
        write_json(ep / "meta/story-gates.json", {"story": {"hook_frames": [1]}})
        write_json(archive / MARKER_NAME, {
            "schema_version": 1, "non_episode": True, "kind": "abandoned_episode_archive",
            "archived_at": "2026-09-11", "archived_from": "episodes/10_demo/03_demo",
            "reason": "self test",
        })
        entry = build_entry(base, ep, written_at="2026-09-11T00:00:00+08:00")
        assert entry["from"] == "episodes/10_demo/03_demo"
        assert entry["to"] == "episodes/_archive/20260911_EP099_abandoned_demo"
        assert entry["prefix_map"][0]["to"].endswith("20260911_EP099_abandoned_demo/")
        story_anchor = next(a for a in entry["anchors"] if a["name"] == "story")
        assert story_anchor["status"] == "relocated", story_anchor
        assert verify(base, entry) == [], verify(base, entry)
        _ = upsert_entry(base, entry)
        assert entry_for(base, ep)["to"] == entry["to"]
        story.write_text("story lock changed\n", encoding="utf-8")
        assert "anchor_hash_drift" in [code for code, _ in verify(base, entry)]
        story.unlink()
        assert "anchor_unresolved" in [code for code, _ in verify(base, entry)]
    print("ARCHIVE RELOCATION SELF-TEST PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("build"); p.add_argument("episode_dir"); p.add_argument("--write", action="store_true")
    p = sub.add_parser("show"); p.add_argument("episode_dir")
    p = sub.add_parser("resolve"); p.add_argument("path")
    p = sub.add_parser("scan"); p.add_argument("episode_dir")
    p = sub.add_parser("verify"); p.add_argument("episode_dir", nargs="?"); p.add_argument("--all", action="store_true")
    sub.add_parser("self-test")
    args = parser.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    if args.cmd == "list":
        print(json.dumps([{"episode_id": e.get("episode_id"), "from": e.get("from"), "to": e.get("to")}
                          for e in registry()], ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "resolve":
        ref = normalize_ref(args.path)
        print(json.dumps(resolve_ref(ROOT, args.path, entry_for_ref(ROOT, ref)), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "show":
        entry = entry_for(ROOT, args.episode_dir) or build_entry(ROOT, args.episode_dir)
        print(json.dumps(entry, ensure_ascii=False, indent=2)); return 0
    if args.cmd == "build":
        entry = build_entry(ROOT, args.episode_dir)
        if args.write:
            upsert_entry(ROOT, entry)
        print(json.dumps(entry, ensure_ascii=False, indent=2)); return 0
    if args.cmd == "scan":
        entry = entry_for(ROOT, args.episode_dir) or build_entry(ROOT, args.episode_dir)
        print(json.dumps(scan_references(ROOT, Path(args.episode_dir).resolve(), entry),
                         ensure_ascii=False, indent=2)); return 0
    if args.cmd == "verify":
        if args.all:
            failed = 0
            for entry in registry():
                findings = verify(ROOT, entry)
                failed += 1 if findings else 0
                print(("FAIL " if findings else "PASS ") + str(entry.get("to")))
                for code, message in findings:
                    print("      " + code + ": " + message)
            return 2 if failed else 0
        if not args.episode_dir:
            print("verify needs <episode_dir> or --all"); return 1
        entry = entry_for(ROOT, args.episode_dir)
        if entry is None:
            print("no relocation entry for " + args.episode_dir + " (run: build --write)"); return 1
        findings = verify(ROOT, entry)
        for code, message in findings:
            print("FAIL: " + code + ": " + message)
        if not findings:
            print("ARCHIVE RELOCATION VERIFIED: " + str(entry.get("to")))
        return 2 if findings else 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

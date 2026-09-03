#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

GATES_FILE = Path("meta/story-gates.json")
MANIFEST_FILE = Path("meta/release-manifest.json")
REVIEW_TEMPLATE = {
    "schema_version": 1,
    "frame": None,
    "viewpoint_physics": "pending",
    "unplanned_recorder_absent": "pending",
    "capture_profile_match": "pending",
    "not_cinematic": "pending",
    "identity_match": "na",
    "key_prop_match": "na",
    "location_match": "na",
    "continuity_match": "pending",
    "defects_are_causal": "na",
    "album_test": "pending",
    "hard_failures_detected": [],
    "red_flags_detected": [],
    "red_flags_exempted": [],
    "intentional_exception": {"enabled": False, "reason": ""},
    "decision": "pending",
    "notes": "",
}
CALIBRATION_ROLES = {"baseline", "worst_condition", "first_major_anomaly"}
REFERENCE_KINDS = {"identity", "prop", "location", "capture_style"}


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return data


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_relative(path: Path) -> str:
    root = repo_root().resolve()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        raise SystemExit(f"asset must live inside repository: {path}")


def episode(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    return ep


def frame_count(ep: Path) -> int:
    manifest = load_json(ep / MANIFEST_FILE)
    value = ((manifest.get("release") or {}).get("body_frame_count"))
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise SystemExit("manifest release.body_frame_count invalid")
    return value


def cmd_init_reviews(args: argparse.Namespace) -> None:
    ep = episode(args.episode_dir)
    total = frame_count(ep)
    gates = load_json(ep / GATES_FILE)
    evidence = gates.setdefault("production_evidence", {})
    rel = evidence.get("frame_review_dir", "meta/frame-reviews")
    out = ep / rel
    out.mkdir(parents=True, exist_ok=True)
    created = 0
    for n in range(1, total + 1):
        path = out / f"{n:02d}.json"
        if path.exists() and not args.force:
            continue
        item = json.loads(json.dumps(REVIEW_TEMPLATE))
        item["frame"] = f"{n:02d}"
        save_json(path, item)
        created += 1
    evidence["frame_review_dir"] = rel
    evidence["require_all_frames"] = True
    evidence["review_schema_version"] = 1
    save_json(ep / GATES_FILE, gates)
    print(f"review templates ready: {out} ({created} created, total={total})")


def cmd_import_review(args: argparse.Namespace) -> None:
    ep = episode(args.episode_dir)
    total = frame_count(ep)
    n = int(args.frame)
    if not 1 <= n <= total:
        raise SystemExit(f"frame must be within 1..{total}")
    src = Path(args.file).resolve()
    if not src.is_file():
        raise SystemExit(f"review file not found: {src}")
    data = load_json(src)
    if str(data.get("frame") or "").zfill(2) != f"{n:02d}":
        raise SystemExit(f"review frame mismatch: expected {n:02d}")
    gates = load_json(ep / GATES_FILE)
    rel = (gates.get("production_evidence") or {}).get("frame_review_dir", "meta/frame-reviews")
    dst = ep / rel / f"{n:02d}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    save_json(dst, data)
    print(f"imported review: {dst}")


def cmd_import_authenticity(args: argparse.Namespace) -> None:
    ep = episode(args.episode_dir)
    src = Path(args.file).resolve()
    card = load_json(src)
    gates = load_json(ep / GATES_FILE)
    visual = gates.setdefault("visual", {})
    visual["authenticity_card"] = card
    save_json(ep / GATES_FILE, gates)
    print("authenticity card imported into story-gates.json")


def cmd_record_calibration(args: argparse.Namespace) -> None:
    if args.role not in CALIBRATION_ROLES:
        raise SystemExit(f"invalid role: {args.role}")
    ep = episode(args.episode_dir)
    total = frame_count(ep)
    n = int(args.frame)
    if not 1 <= n <= total:
        raise SystemExit(f"frame must be within 1..{total}")
    asset = Path(args.asset).resolve()
    if not asset.is_file():
        raise SystemExit(f"asset not found: {asset}")
    gates = load_json(ep / GATES_FILE)
    visual = gates.setdefault("visual", {})
    calibration = visual.setdefault("calibration", {})
    calibration[args.role] = {
        "frame": n,
        "asset_path": repo_relative(asset),
        "sha256": sha256_file(asset),
        "decision": args.decision,
        "note": args.note,
    }
    save_json(ep / GATES_FILE, gates)
    print(f"recorded calibration {args.role}: frame={n:02d}")


def cmd_register_reference(args: argparse.Namespace) -> None:
    if args.kind not in REFERENCE_KINDS:
        raise SystemExit(f"invalid kind: {args.kind}")
    ep = episode(args.episode_dir)
    asset = Path(args.asset).resolve()
    if not asset.is_file():
        raise SystemExit(f"asset not found: {asset}")
    gates = load_json(ep / GATES_FILE)
    refs = gates.setdefault("visual", {}).setdefault("references", {"required": False, "required_anchors": [], "items": []})
    items = refs.setdefault("items", [])
    item = {
        "id": args.id,
        "anchor": args.anchor,
        "kind": args.kind,
        "path": repo_relative(asset),
        "sha256": sha256_file(asset),
        "decision": args.decision,
        "note": args.note,
    }
    replaced = False
    for idx, old in enumerate(items):
        if isinstance(old, dict) and old.get("id") == args.id:
            items[idx] = item
            replaced = True
            break
    if not replaced:
        items.append(item)
    save_json(ep / GATES_FILE, gates)
    print(f"{'updated' if replaced else 'registered'} reference {args.id}")


def cmd_reference_policy(args: argparse.Namespace) -> None:
    ep = episode(args.episode_dir)
    gates = load_json(ep / GATES_FILE)
    refs = gates.setdefault("visual", {}).setdefault("references", {"required": False, "required_anchors": [], "items": []})
    refs["required"] = args.required
    refs["required_anchors"] = list(dict.fromkeys(args.anchor or []))
    save_json(ep / GATES_FILE, gates)
    print(f"reference policy: required={args.required}, anchors={refs['required_anchors']}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DALI CAT Story OS evidence recorder V1.5")
    sub = p.add_subparsers(dest="command", required=True)

    x = sub.add_parser("init-reviews", help="create per-frame structured authenticity review templates")
    x.add_argument("episode_dir")
    x.add_argument("--force", action="store_true")
    x.set_defaults(func=cmd_init_reviews)

    x = sub.add_parser("import-review", help="copy a completed structured review into the episode evidence directory")
    x.add_argument("episode_dir")
    x.add_argument("frame")
    x.add_argument("--file", required=True)
    x.set_defaults(func=cmd_import_review)

    x = sub.add_parser("import-authenticity", help="store project-level authenticity card in story-gates.json")
    x.add_argument("episode_dir")
    x.add_argument("--file", required=True)
    x.set_defaults(func=cmd_import_authenticity)

    x = sub.add_parser("record-calibration", help="LEGACY_ONLY: lock one of the three realism calibration frames by SHA-256")
    x.add_argument("episode_dir")
    x.add_argument("--role", required=True, choices=sorted(CALIBRATION_ROLES))
    x.add_argument("--frame", required=True)
    x.add_argument("--asset", required=True)
    x.add_argument("--decision", choices=["passed", "failed"], required=True)
    x.add_argument("--note", default="")
    x.set_defaults(func=cmd_record_calibration)

    x = sub.add_parser("register-reference", help="register a continuity reference asset and freeze its hash")
    x.add_argument("episode_dir")
    x.add_argument("--id", required=True)
    x.add_argument("--anchor", required=True)
    x.add_argument("--kind", required=True, choices=sorted(REFERENCE_KINDS))
    x.add_argument("--asset", required=True)
    x.add_argument("--decision", choices=["passed", "failed"], default="passed")
    x.add_argument("--note", default="")
    x.set_defaults(func=cmd_register_reference)

    x = sub.add_parser("reference-policy", help="declare whether this episode requires reference assets")
    x.add_argument("episode_dir")
    g = x.add_mutually_exclusive_group(required=True)
    g.add_argument("--required", action="store_true")
    g.add_argument("--optional", dest="required", action="store_false")
    x.add_argument("--anchor", action="append", default=[])
    x.set_defaults(func=cmd_reference_policy)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

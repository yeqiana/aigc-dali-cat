#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EPISODES = ROOT / "episodes"
MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".tif", ".tiff", ".svg", ".mp4", ".mov", ".avi", ".mkv", ".wav", ".mp3", ".flac", ".zip"}
TEXT_EXTS = {".json", ".md", ".yaml", ".yml", ".txt", ".csv", ".py"}
INDEX_REL = Path("meta/media-index.json")
BACKUP_ROOT = ROOT / ".story-os-media-migration"


def now_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_git(args: list[str], *, binary: bool = False) -> bytes | str:
    cp = subprocess.run(["git", *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.decode("utf-8", errors="replace") or f"git {' '.join(args)} failed")
    return cp.stdout if binary else cp.stdout.decode("utf-8", errors="replace")


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def episode_for(path: Path) -> Path | None:
    cur = path.parent.resolve()
    stop = EPISODES.resolve()
    while cur != stop and stop in cur.parents:
        if (cur / "meta/episode-state.json").is_file():
            return cur
        cur = cur.parent
    return None


FROZEN_STATES = {"PRODUCTION_PASSED", "PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}


def episode_state(ep: Path) -> str | None:
    path = ep / "meta/episode-state.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    state = data.get("current_state")
    return str(state) if state else None


def evidence_frozen(ep: Path) -> bool:
    """Do not move path-bound media after production/release evidence has been sealed."""
    state = episode_state(ep)
    if state in FROZEN_STATES:
        return True
    return (ep / "meta/delegated-release.json").is_file()


def ignored_media() -> list[Path]:
    raw = run_git(["ls-files", "--others", "-i", "--exclude-standard", "-z", "--", "episodes"], binary=True)
    out: list[Path] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        rel = item.decode("utf-8", errors="surrogateescape")
        p = ROOT / rel
        if p.is_file() and p.suffix.lower() in MEDIA_EXTS:
            out.append(p)
    return sorted(out)


def classify(ep: Path, src: Path) -> Path:
    rel = src.relative_to(ep)
    low_parts = [p.lower() for p in rel.parts]
    low = "/".join(low_parts)
    suffix = src.suffix.lower()
    name = src.name.lower()

    if low.startswith("media/") or low.startswith("release/") or low.startswith("assets/references/"):
        return src
    if "calibration" in low or "校准" in low:
        return ep / "media/calibration" / src.name
    if "contact" in low or "review" in low or "sheet" in low or "/qa/" in f"/{low}/":
        return ep / "media/review" / src.name
    if suffix == ".zip" or "delivery" in low or "交付" in low:
        return ep / "release" / src.name
    if "cover" in name or "封面" in name:
        return ep / "release" / src.name
    if "publish" in low or "subtitled" in low or "字幕" in low:
        return ep / "media/publish" / src.name
    if "production/raw" in low or "/raw/" in f"/{low}/":
        return ep / "media/raw" / src.name
    if "approved" in low or re.search(r"(?:^|[_-])(final|approved|lock)(?:[_\-.]|$)", name):
        return ep / "media/approved" / src.name
    if any(token in low for token in ("candidate", "repair", "repairs", "fix", "tmp", "originals")):
        return ep / "media/candidates" / src.name
    if "assets/references" in low or "reference" in low or "references" in low:
        return ep / "assets/references" / src.name
    return ep / "media/archive/legacy" / rel


def unique_dest(dst: Path, src_sha: str) -> Path:
    if not dst.exists():
        return dst
    try:
        if dst.is_file() and sha256_file(dst) == src_sha:
            # Keep one canonical copy; caller may safely remove source after verification.
            return dst
    except OSError:
        pass
    return dst.with_name(f"{dst.stem}__{src_sha[:8]}{dst.suffix}")


def tracked_text_files(ep: Path) -> list[Path]:
    rel = repo_rel(ep)
    out = run_git(["ls-files", "-z", "--", rel], binary=True)
    files: list[Path] = []
    for item in out.split(b"\0"):
        if not item:
            continue
        p = ROOT / item.decode("utf-8", errors="surrogateescape")
        if p.is_file() and p.suffix.lower() in TEXT_EXTS:
            files.append(p)
    return files


def replace_references(ep: Path, mapping: dict[str, str], backup_dir: Path) -> list[str]:
    changed: list[str] = []
    if not mapping:
        return changed
    ep_rel = repo_rel(ep)
    for path in tracked_text_files(ep):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        original = text
        for old_repo, new_repo in mapping.items():
            old_ep = old_repo[len(ep_rel) + 1:] if old_repo.startswith(ep_rel + "/") else None
            new_ep = new_repo[len(ep_rel) + 1:] if new_repo.startswith(ep_rel + "/") else None
            pairs = [(old_repo, new_repo), (old_repo.replace("/", "\\"), new_repo.replace("/", "\\"))]
            if old_ep and new_ep:
                pairs += [(old_ep, new_ep), (old_ep.replace("/", "\\"), new_ep.replace("/", "\\"))]
            for old, new in pairs:
                text = text.replace(old, new)
        if text != original:
            rel = path.relative_to(ROOT)
            backup = backup_dir / "tracked" / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
            path.write_text(text, encoding="utf-8", newline="\n")
            changed.append(rel.as_posix())
    return changed


def normalize_ledger_roots(ep: Path, backup_dir: Path) -> bool:
    path = ep / "meta/production-ledger.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    desired = {
        "originals": "media/candidates/originals",
        "repairs": "media/candidates/repairs",
        "approved": "media/approved",
        "publish": "media/publish",
        "contact_sheets": "media/review/contact-sheets",
    }
    if data.get("asset_roots") == desired:
        return False
    rel = path.relative_to(ROOT)
    backup = backup_dir / "tracked" / rel
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
    data["asset_roots"] = desired
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return True


def ensure_layout(ep: Path) -> None:
    for rel in (
        "media/calibration", "media/raw", "media/candidates", "media/approved", "media/publish",
        "media/review", "media/archive", "assets/references", "release", "meta",
    ):
        (ep / rel).mkdir(parents=True, exist_ok=True)


def build_index(ep: Path) -> dict:
    items: list[dict] = []
    roots = [ep / "media", ep / "release", ep / "assets/references"]
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in MEDIA_EXTS:
                items.append({
                    "path": repo_rel(path),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "kind": path.relative_to(ep).parts[0],
                })
    return {
        "schema_version": 1,
        "story_os_version": "2.0.3.4",
        "policy": "local_media_not_git_payload",
        "episode": repo_rel(ep),
        "item_count": len(items),
        "items": items,
    }


def write_index(ep: Path) -> None:
    data = build_index(ep)
    p = ep / INDEX_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def migration_plan() -> dict:
    ignored = ignored_media()
    managed: list[dict] = []
    frozen: list[dict] = []
    legacy_unmanaged: list[str] = []
    for src in ignored:
        ep = episode_for(src)
        if ep is None:
            legacy_unmanaged.append(repo_rel(src))
            continue
        item = {"episode": repo_rel(ep), "source": repo_rel(src), "sha256": sha256_file(src), "bytes": src.stat().st_size}
        if evidence_frozen(ep):
            item["state"] = episode_state(ep)
            frozen.append(item)
            continue
        dst = classify(ep, src)
        item["target"] = repo_rel(dst)
        managed.append(item)
    return {
        "schema_version": 2,
        "generated_at": now_stamp(),
        "policy": "never_move_frozen_path_bound_evidence",
        "managed_count": len(managed),
        "managed": managed,
        "frozen_skipped_count": len(frozen),
        "frozen_skipped": frozen,
        "legacy_unmanaged_count": len(legacy_unmanaged),
        "legacy_unmanaged": legacy_unmanaged,
    }


def migrate(*, dry_run: bool = False) -> dict:
    plan = migration_plan()
    if dry_run:
        return plan
    stamp = now_stamp()
    backup_dir = BACKUP_ROOT / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    moves: list[tuple[Path, Path]] = []
    per_episode_mapping: dict[Path, dict[str, str]] = {}
    touched_eps: set[Path] = set()
    try:
        for item in plan["managed"]:
            src = ROOT / item["source"]
            if not src.exists():
                continue
            ep = ROOT / item["episode"]
            ensure_layout(ep)
            dst0 = ROOT / item["target"]
            if src.resolve() == dst0.resolve():
                touched_eps.add(ep)
                continue
            src_sha = item["sha256"]
            dst = unique_dest(dst0, src_sha)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() and sha256_file(dst) == src_sha:
                # Canonical identical copy already exists; source is still preserved until final verification.
                pass
            else:
                shutil.copy2(src, dst)
                if sha256_file(dst) != src_sha:
                    raise RuntimeError(f"SHA mismatch after copy: {src} -> {dst}")
            moves.append((src, dst))
            touched_eps.add(ep)
            per_episode_mapping.setdefault(ep, {})[repo_rel(src)] = repo_rel(dst)

        changed_refs: dict[str, list[str]] = {}
        for ep, mapping in per_episode_mapping.items():
            changed_refs[repo_rel(ep)] = replace_references(ep, mapping, backup_dir)
            if normalize_ledger_roots(ep, backup_dir):
                changed_refs[repo_rel(ep)].append(repo_rel(ep / "meta/production-ledger.json"))

        # Verify destinations and rewritten references before removing old files.
        for src, dst in moves:
            if not dst.is_file() or sha256_file(src) != sha256_file(dst):
                raise RuntimeError(f"pre-delete verification failed: {src} -> {dst}")

        for src, dst in moves:
            if src.exists() and src.resolve() != dst.resolve():
                src.unlink()
                # Remove empty legacy directories, but never walk above episode root.
                ep = episode_for(dst) or episode_for(src)
                cur = src.parent
                while ep is not None and cur != ep and cur.exists():
                    try:
                        cur.rmdir()
                    except OSError:
                        break
                    cur = cur.parent

        for ep in touched_eps:
            write_index(ep)

        result = {
            **plan,
            "status": "COMPLETE",
            "backup_dir": repo_rel(backup_dir),
            "moved_count": len(moves),
            "moves": [{"source": repo_rel(src), "target": repo_rel(dst), "sha256": sha256_file(dst)} for src, dst in moves],
            "changed_references": changed_refs,
            "touched_episodes": sorted(repo_rel(x) for x in touched_eps),
        }
        (backup_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
    except Exception as exc:
        # Best-effort rollback: copied destinations are removed only when source still exists;
        # rewritten tracked files are restored from backup.
        for backup in sorted((backup_dir / "tracked").rglob("*")) if (backup_dir / "tracked").exists() else []:
            if backup.is_file():
                rel = backup.relative_to(backup_dir / "tracked")
                target = ROOT / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)
        for src, dst in reversed(moves):
            if not src.exists() and dst.exists():
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, src)
            if src.exists() and dst.exists() and src.resolve() != dst.resolve():
                try:
                    if sha256_file(src) == sha256_file(dst):
                        dst.unlink()
                except OSError:
                    pass
        failure = {**plan, "status": "ROLLED_BACK", "error": str(exc), "backup_dir": repo_rel(backup_dir)}
        (backup_dir / "result.json").write_text(json.dumps(failure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise


def restore(backup_raw: str) -> dict:
    backup_dir = Path(backup_raw)
    backup_dir = backup_dir.resolve() if backup_dir.is_absolute() else (ROOT / backup_dir).resolve()
    result_path = backup_dir / "result.json"
    if not result_path.is_file():
        raise RuntimeError(f"migration result missing: {result_path}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    restored_files = []
    tracked_root = backup_dir / "tracked"
    if tracked_root.exists():
        for backup in sorted(tracked_root.rglob("*")):
            if backup.is_file():
                rel = backup.relative_to(tracked_root)
                target = ROOT / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)
    for item in reversed(result.get("moves") or []):
        src = ROOT / item["source"]
        dst = ROOT / item["target"]
        if dst.is_file():
            src.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, src)
            if sha256_file(src) != str(item.get("sha256") or ""):
                raise RuntimeError(f"restore SHA mismatch: {src}")
            restored_files.append(repo_rel(src))
            if src.resolve() != dst.resolve():
                dst.unlink()
    restored = {"status": "RESTORED", "backup_dir": repo_rel(backup_dir), "restored_files": restored_files}
    (backup_dir / "restore.json").write_text(json.dumps(restored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return restored


def ensure_all_managed() -> list[str]:
    eps = sorted({p.parent.parent for p in EPISODES.rglob("meta/episode-state.json")})
    for ep in eps:
        ensure_layout(ep)
        write_index(ep)
    return [repo_rel(ep) for ep in eps]


def main() -> int:
    ap = argparse.ArgumentParser(description="Story OS V2.0.3.4 local media workspace manager")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("inventory"); p.add_argument("--output")
    p = sub.add_parser("migrate"); p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("ensure"); p.add_argument("episode_dir")
    p = sub.add_parser("restore"); p.add_argument("backup_dir")
    sub.add_parser("ensure-all")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        assert ".png" in MEDIA_EXTS
        assert classify(Path("/tmp/ep"), Path("/tmp/ep/production/raw/a.png")).as_posix().endswith("/media/raw/a.png")
        assert classify(Path("/tmp/ep"), Path("/tmp/ep/publish/01.png")).as_posix().endswith("/media/publish/01.png")
        print("MEDIA WORKSPACE SELF-TEST PASS")
        return 0
    if args.cmd == "inventory":
        data = migration_plan()
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    if args.cmd == "migrate":
        data = migrate(dry_run=args.dry_run)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "ensure":
        ep = Path(args.episode_dir).resolve()
        ensure_layout(ep); write_index(ep); print(f"MEDIA WORKSPACE READY: {repo_rel(ep)}"); return 0
    if args.cmd == "restore":
        print(json.dumps(restore(args.backup_dir), ensure_ascii=False, indent=2)); return 0
    eps = ensure_all_managed(); print(json.dumps({"episodes": eps}, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())

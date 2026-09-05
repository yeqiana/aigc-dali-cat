#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, re, shutil, tempfile
from pathlib import Path

PNG = b"\x89PNG\r\n\x1a\n"
JPEG = b"\xff\xd8\xff"

def valid_image(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 16:
        return False
    head = path.read_bytes()[:16]
    return head.startswith(PNG) or head.startswith(JPEG)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def atomic_write_bytes(path: Path, data: bytes) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as h:
            h.write(data)
            h.flush()
            os.fsync(h.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            Path(temp_name).unlink(missing_ok=True)
        except OSError:
            pass
    if not valid_image(path):
        raise ValueError(f"provider output is not a valid PNG/JPEG: {path}")
    return {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}

def _thread_ids(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except Exception:
            continue
        if not isinstance(row, dict) or row.get("type") != "thread.started":
            continue
        thread_id = str(row.get("thread_id") or "").strip()
        if thread_id and thread_id not in out:
            out.append(thread_id)
    return out


def _local_fallback_allowed(workdir: Path) -> bool:
    return Path(workdir).name.startswith("story-os-image-")


def recover_codex_generated(log: Path, workdir: Path) -> Path | None:
    candidates: list[Path] = []
    if log.is_file():
        text = log.read_text(encoding="utf-8", errors="replace")
        # Primary recovery: use the exact Codex thread directory so parallel workers cannot cross-pick images.
        for thread_id in _thread_ids(text):
            thread_dir = Path.home() / ".codex" / "generated_images" / thread_id
            if not thread_dir.is_dir():
                continue
            try:
                for probe in thread_dir.rglob("*"):
                    if probe.is_file() and probe.suffix.lower() in {".png", ".jpg", ".jpeg"} and valid_image(probe):
                        candidates.append(probe.resolve())
            except OSError:
                pass
        # Compatibility recovery for logs that contain an explicit generated image path.
        for raw in re.findall(r'(?i)(?:[A-Za-z]:)?[^"\'\r\n]*?\.codex[\\/]+generated_images[\\/]+[^"\'\r\n]+?\.(?:png|jpe?g)', text):
            cleaned = raw.strip().replace("\\\\", "\\")
            p = Path(cleaned)
            probes = [p]
            if not p.is_absolute():
                probes += [workdir / p, Path.home() / p]
            for probe in probes:
                try:
                    if valid_image(probe.resolve()):
                        candidates.append(probe.resolve())
                except OSError:
                    pass
    # Compatibility fallback is allowed only inside Story OS's dedicated per-worker temp dir.
    # Never let a caller accidentally point this at the repository/home and cross-pick an unrelated image.
    if _local_fallback_allowed(workdir):
        try:
            for p in workdir.rglob("*"):
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"} and not p.name.startswith("reference-"):
                    if valid_image(p):
                        candidates.append(p.resolve())
        except OSError:
            pass
    if not candidates:
        return None
    return max(set(candidates), key=lambda p: p.stat().st_mtime_ns)

def self_test() -> None:
    assert valid_image(Path("__missing__")) is False
    sample='{"type":"thread.started","thread_id":"abc-123"}\n{"type":"item.completed"}'
    assert _thread_ids(sample) == ["abc-123"]
    assert _local_fallback_allowed(Path("story-os-image-abc")) is True
    assert _local_fallback_allowed(Path("repository-root")) is False
    print("IMAGE ARTIFACT COLLECTOR V2.6.1 THREAD-SCOPED SELF-TEST PASS")

if __name__ == "__main__":
    self_test()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explicit provisioning for optional local vision sidecar assets.

This command is an operator action, never called by StoryOS runtime. It may
create an isolated venv and download explicitly selected model snapshots.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".storyos_cache"
VENV = CACHE / "ml-venv"
VENV_PYTHON = VENV / "Scripts" / "python.exe"
MODELS = CACHE / "models"

MODEL_SPECS = {
    "sam2-tiny": {
        "repo_id": "facebook/sam2.1-hiera-tiny",
        "target": MODELS / "sam2.1-hiera-tiny",
        "allow_patterns": [
            "config.json", "model.safetensors", "preprocessor_config.json",
            "processor_config.json", "video_preprocessor_config.json",
        ],
        "required_files": ["config.json", "model.safetensors"],
    },
    "grounding-dino-tiny": {
        "repo_id": "IDEA-Research/grounding-dino-tiny",
        "target": MODELS / "grounding-dino-tiny",
        "allow_patterns": [
            "config.json", "model.safetensors", "preprocessor_config.json",
            "added_tokens.json", "special_tokens_map.json", "tokenizer.json",
            "tokenizer_config.json", "vocab.txt",
        ],
        "required_files": ["config.json", "model.safetensors"],
    },
}


def run(argv: list[str]) -> None:
    completed = subprocess.run(argv, cwd=str(CACHE), check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed rc={completed.returncode}: {argv}")


def ensure_venv() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    if not VENV_PYTHON.is_file():
        run([sys.executable, "-m", "venv", "--system-site-packages", str(VENV)])
    return VENV_PYTHON


def install_transformers() -> None:
    python = ensure_venv()
    req = Path(__file__).with_name("requirements-vision-transformers.txt")
    run([str(python), "-m", "pip", "install", "-r", str(req)])


def download_model(name: str) -> None:
    spec = MODEL_SPECS[name]
    python = ensure_venv()
    target = Path(spec["target"])
    target.mkdir(parents=True, exist_ok=True)
    code = (
        "from huggingface_hub import snapshot_download;"
        "import json,sys;"
        "snapshot_download(repo_id=sys.argv[1],local_dir=sys.argv[2],"
        "allow_patterns=json.loads(sys.argv[3]))"
    )
    run([
        str(python), "-c", code, spec["repo_id"], str(target),
        json.dumps(spec["allow_patterns"]),
    ])


def _model_status(spec: dict) -> dict:
    target = Path(spec["target"])
    allowed = {str(value).replace("\\", "/") for value in spec.get("allow_patterns") or []}
    required = {str(value).replace("\\", "/") for value in spec.get("required_files") or []}
    files = []
    found = set()
    total = 0
    if target.is_dir():
        for path in sorted(target.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(target).as_posix()
            if rel not in allowed:
                continue
            size = path.stat().st_size
            total += size
            found.add(rel)
            files.append({"path": rel, "bytes": size})
    missing = sorted(required - found)
    complete = bool(required) and not missing
    return {
        "repo_id": spec["repo_id"],
        "target": target.relative_to(ROOT).as_posix(),
        "present": complete,
        "complete": complete,
        "partial": bool(files) and not complete,
        "missing_required": missing,
        "total_model_bytes": total,
        "files": files,
    }


def status() -> dict:
    rows = {name: _model_status(spec) for name, spec in MODEL_SPECS.items()}
    return {
        "schema_version": 1,
        "venv_python": str(VENV_PYTHON),
        "venv_present": VENV_PYTHON.is_file(),
        "models": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("create-venv")
    sub.add_parser("install-transformers")
    p = sub.add_parser("download")
    p.add_argument("model", choices=sorted(MODEL_SPECS))
    args = parser.parse_args()
    try:
        if args.command == "status":
            print(json.dumps(status(), ensure_ascii=False, indent=2))
        elif args.command == "create-venv":
            print(ensure_venv())
        elif args.command == "install-transformers":
            install_transformers()
            print("TRANSFORMERS SIDE-CAR DEPENDENCIES INSTALLED")
        elif args.command == "download":
            download_model(args.model)
            print(json.dumps(status()["models"][args.model], ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"LOCAL VISION PROVISION ERROR: {type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

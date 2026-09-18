#!/usr/bin/env python3
"""Stable persistence identity for Story OS Episodes.

The legacy ``episode_id`` is a human/business label and is not globally unique
across series.  Durable stores therefore use a separate deterministic UID based
on the canonical Episode namespace.  The business id remains available for
display, import/export and compatibility evidence.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import runtime_workspace
import story_json


def business_episode_id(ep: str | Path) -> str:
    ep = Path(ep).resolve()
    state = story_json.read_json(ep / "meta/episode-state.json", default={}) or {}
    return str(state.get("episode_id") or state.get("id") or ep.name).strip()


def episode_namespace(ep: str | Path) -> str:
    return runtime_workspace.episode_namespace(Path(ep).resolve()).as_posix()


def storage_episode_id(ep: str | Path) -> str:
    """Return a globally unique, deterministic <=64 char Episode storage UID."""
    ep = Path(ep).resolve()
    state = story_json.read_json(ep / "meta/episode-state.json", default={}) or {}
    explicit = str(state.get("storage_episode_id") or "").strip()
    if explicit:
        return explicit
    material = f"{episode_namespace(ep).casefold()}|{business_episode_id(ep).casefold()}"
    return "EPU_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:40]


def identity_record(ep: str | Path) -> dict:
    ep = Path(ep).resolve()
    state = story_json.read_json(ep / "meta/episode-state.json", default={}) or {}
    return {
        "storage_episode_id": storage_episode_id(ep),
        "business_episode_id": business_episode_id(ep),
        "namespace": episode_namespace(ep),
        "series": str(state.get("series") or "").strip() or None,
        "title": str(state.get("title") or ep.name).strip(),
    }

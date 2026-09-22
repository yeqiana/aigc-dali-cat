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
import episode_state_persistence


def _state(ep: str | Path) -> dict:
    return episode_state_persistence.load(Path(ep).resolve()) or {}


def storage_episode_id_from_business(ep: str | Path, business_episode_id: str) -> str:
    ep = Path(ep).resolve()
    material = f"{episode_namespace(ep).casefold()}|{str(business_episode_id).casefold()}"
    return "EPU_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:40]


def business_episode_id(ep: str | Path) -> str:
    ep = Path(ep).resolve()
    state = _state(ep)
    return str(state.get("episode_id") or state.get("id") or ep.name).strip()


def episode_namespace(ep: str | Path) -> str:
    return runtime_workspace.episode_namespace(Path(ep).resolve()).as_posix()


def storage_episode_id(ep: str | Path) -> str:
    """Return a globally unique, deterministic <=64 char Episode storage UID."""
    ep = Path(ep).resolve()
    state = _state(ep)
    explicit = str(state.get("storage_episode_id") or "").strip()
    if explicit:
        return explicit
    return storage_episode_id_from_business(ep, business_episode_id(ep))


def identity_record(ep: str | Path) -> dict:
    ep = Path(ep).resolve()
    state = _state(ep)
    return {
        "storage_episode_id": storage_episode_id(ep),
        "business_episode_id": business_episode_id(ep),
        "namespace": episode_namespace(ep),
        "series": str(state.get("series") or "").strip() or None,
        "title": str(state.get("title") or ep.name).strip(),
    }

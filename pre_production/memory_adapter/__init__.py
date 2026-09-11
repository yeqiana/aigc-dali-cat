#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memory Adapter: read historical experience, persist Review References."""
from __future__ import annotations

from .adapter import DEFAULT_STORE_DIR, MemoryAdapter

__all__ = ["MemoryAdapter", "DEFAULT_STORE_DIR"]


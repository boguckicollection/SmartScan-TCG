"""Mapping of set abbreviations to their full names."""

from __future__ import annotations

import json
from pathlib import Path

_data_file = Path(__file__).resolve().parent.parent / "data" / "tcg_sets.json"

try:
    with open(_data_file, "r", encoding="utf-8") as f:
        SET_MAP: dict[str, str] = json.load(f)
except Exception:
    SET_MAP = {}

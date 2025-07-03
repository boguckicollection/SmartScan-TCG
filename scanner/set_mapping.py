"""Mapping of set abbreviations to their full names."""

from __future__ import annotations

import json
from pathlib import Path

_data_file = Path(__file__).resolve().parent.parent / "data" / "tcg_sets.json"
_data_file_jp = Path(__file__).resolve().parent.parent / "data" / "tcg_sets_jp.json"

SET_MAP_EN: dict[str, str]
SET_MAP_JP: dict[str, str]

try:
    with open(_data_file, "r", encoding="utf-8") as f:
        SET_MAP_EN = json.load(f)
except Exception:
    SET_MAP_EN = {}

try:
    with open(_data_file_jp, "r", encoding="utf-8") as f:
        SET_MAP_JP = json.load(f)
except Exception:
    SET_MAP_JP = {}

SET_MAP: dict[str, str] = SET_MAP_EN

# Mapping of set abbreviations to a list of available names (EN/JP)
SET_NAMES: dict[str, list[str]] = {}
for key in set(SET_MAP_EN) | set(SET_MAP_JP):
    names = []
    en = SET_MAP_EN.get(key)
    if en:
        names.append(en)
    jp = SET_MAP_JP.get(key)
    if jp and jp not in names:
        names.append(jp)
    if names:
        SET_NAMES[key] = names

# Reverse lookup of any set name back to its abbreviation
INV_SET_MAP: dict[str, str] = {}
for abbr, names in SET_NAMES.items():
    for n in names:
        INV_SET_MAP[n] = abbr

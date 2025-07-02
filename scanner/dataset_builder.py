from __future__ import annotations

"""Utilities for building a labeled image dataset from card scans."""

from pathlib import Path
import csv
from typing import List, Dict

from .card_scanner import scan_image
from .image_analyzer import analyze_image


def gather_scan_paths(scan_dir: str | Path) -> List[Path]:
    """Return sorted list of image paths within ``scan_dir``."""
    directory = Path(scan_dir)
    files: List[Path] = []
    for pattern in ("*.jpg", "*.png"):
        files.extend(sorted(directory.glob(pattern)))
    return files


def label_image(path: Path) -> Dict[str, object]:
    """Return dataset row for ``path`` combining scan and analysis."""
    card_data = scan_image(path)
    image_data = analyze_image(str(path))

    set_name = card_data.get("Set", "Unknown")
    number = card_data.get("Number", "")
    name = card_data.get("Name", "Unknown")
    card_id = f"{set_name}-{number}" if set_name and number else ""

    return {
        "image_path": str(path),
        "name": name,
        "card_id": card_id,
        "set": set_name,
        "holo": bool(image_data.get("holo")),
        "reverse": bool(image_data.get("reverse")),
    }


def build_dataset(scan_dir: str | Path, csv_path: str | Path | None = None) -> List[Dict[str, object]]:
    """Gather scans from ``scan_dir`` and save labeled data to CSV."""
    paths = gather_scan_paths(scan_dir)
    rows = [label_image(p) for p in paths]

    if csv_path is None:
        csv_path = Path(__file__).resolve().parent / "dataset.csv"
    out = Path(csv_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["image_path", "name", "card_id", "set", "holo", "reverse"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows

"""Batch scanner for extracting data from card images."""

from pathlib import Path
import os
import re
import sys
import tempfile

# Allow running the script directly from the ``scanner`` directory
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use absolute imports so the script can be executed directly
# or via ``python -m`` without package issues.
from scanner.ocr_engine import extract_text
from PIL import Image
from scanner.data_exporter import export_to_csv

RARITY_KEYWORDS = [
    "Common",
    "Uncommon",
    "Rare",
    "Ultra Rare",
    "Secret Rare",
    "Promo",
]


def _extract_text_compat(path: str, bbox: tuple | None) -> str:
    """Call :func:`extract_text` with optional bounding box support.

    Older versions of :func:`extract_text` did not accept a ``bbox`` keyword
    argument.  This helper catches ``TypeError`` and falls back to cropping the
    image manually before calling ``extract_text`` again without ``bbox``.
    """
    try:
        return extract_text(path, bbox=bbox)
    except TypeError:
        image = Image.open(path)
        if bbox:
            image = image.crop(bbox)
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(path).suffix) as tmp:
            tmp_path = tmp.name
        image.save(tmp_path)
        try:
            return extract_text(tmp_path)
        finally:
            os.remove(tmp_path)


def parse_card_text(text: str, name_override: str | None = None) -> dict:
    """Parse OCR text and return card attributes."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines else "Unknown"
    if name_override:
        name = name_override

    number_match = re.search(r"(\d+/\d+)", text)
    number = number_match.group(1) if number_match else ""

    rarity = ""
    for r in RARITY_KEYWORDS:
        if re.search(r, text, re.IGNORECASE):
            rarity = r
            break

    set_match = re.search(r"Set[:\s]*(.+)", text, re.IGNORECASE)
    set_name = set_match.group(1).strip() if set_match else ""

    return {"Name": name, "Set": set_name, "Rarity": rarity, "Number": number}


def scan_image(path: Path) -> dict:
    """Scan a single image and return parsed data."""
    image = Image.open(path)
    width, height = image.size

    # Name is typically in the upper part of the card
    name_bbox = (0, 0, width // 2, int(height * 0.15))
    name_text = _extract_text_compat(str(path), name_bbox)
    name_line = name_text.splitlines()[0].strip() if name_text.splitlines() else "Unknown"

    # Set info and number usually reside near the bottom right
    info_bbox = (width // 2, int(height * 0.8), width, height)
    info_text = _extract_text_compat(str(path), info_bbox)

    return parse_card_text(info_text, name_override=name_line)


def scan_directory(dir_path: Path) -> list:
    """Scan all images in the given directory."""
    results = []
    for img_path in sorted(Path(dir_path).glob("*.jpg")):
        results.append(scan_image(img_path))
    for img_path in sorted(Path(dir_path).glob("*.png")):
        results.append(scan_image(img_path))
    return results


def scan_files(files: list[Path]) -> list:
    """Scan a list of image paths."""
    results = []
    for img_path in files:
        results.append(scan_image(img_path))
    return results


def main():
    scans_dir = Path("assets/scans")
    output_path = Path("data/cards_scanned.csv")
    data = scan_directory(scans_dir)
    export_to_csv(data, str(output_path))
    print(f"Saved {len(data)} records to {output_path}")


if __name__ == "__main__":
    main()

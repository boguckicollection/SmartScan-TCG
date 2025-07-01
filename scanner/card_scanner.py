"""Batch scanner for extracting data from card images."""

from pathlib import Path
from collections import defaultdict
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


def parse_card_text(name_text: str, number_text: str) -> dict:
    """Parse card name and additional info from OCR text fragments."""
    # Name comes from the upper crop of the card image
    name_lines = [line.strip() for line in name_text.splitlines() if line.strip()]
    name = name_lines[0] if name_lines else "Unknown"

    # Number, set and rarity usually appear near the bottom of the card
    combined = "\n".join(
        line.strip() for line in number_text.splitlines() if line.strip()
    )

    number_match = re.search(r"(\d+/\d+)", combined)
    number = number_match.group(1) if number_match else ""

    rarity = ""
    for r in RARITY_KEYWORDS:
        if re.search(r, combined, re.IGNORECASE):
            rarity = r
            break

    set_match = re.search(r"Set[:\s]*(.+)", combined, re.IGNORECASE)
    set_name = set_match.group(1).strip() if set_match else ""

    return {"Name": name, "Set": set_name, "Rarity": rarity, "Number": number}


def scan_image(path: Path) -> dict:
    """Scan a single image and return parsed data."""
    image = Image.open(path)
    width, height = image.size

    # Name: top 10% of the card, cropped with horizontal margins
    name_bbox = (
        int(width * 0.1),
        0,
        int(width * 0.9),
        int(height * 0.1),
    )
    name_text = _extract_text_compat(str(path), name_bbox)

    # Number and other info: bottom 15% of the card, near the right edge
    number_bbox = (
        int(width * 0.6),
        int(height * 0.85),
        int(width * 0.95),
        height,
    )
    number_text = _extract_text_compat(str(path), number_bbox)

    return parse_card_text(name_text, number_text)


def scan_directory(dir_path: Path) -> list:
    """Scan all images in the given directory."""
    results = []
    for ext in ("*.jpg", "*.png"):
        for img_path in sorted(Path(dir_path).glob(ext)):
            results.append(scan_image(img_path))
    return results


def scan_files(files: list[Path]) -> list:
    """Scan a list of image paths."""
    results = []
    for img_path in files:
        results.append(scan_image(img_path))
    return results


def aggregate_cards(data: list[dict]) -> list[dict]:
    """Aggregate duplicate cards by name and number."""
    aggregated: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"Name": "", "Number": "", "Ilość": 0}
    )
    for card in data:
        key = (card.get("Name", ""), card.get("Number", ""))
        aggregated[key]["Name"] = card.get("Name", "")
        aggregated[key]["Number"] = card.get("Number", "")
        aggregated[key]["Ilość"] += 1
    return list(aggregated.values())


def main():
    scans_dir = Path("assets/scans")
    output_path = Path("data/cards_scanned.csv")
    scanned_data = scan_directory(scans_dir)
    grouped_data = aggregate_cards(scanned_data)
    export_to_csv(grouped_data, str(output_path))
    print(f"Zapisano {len(grouped_data)} rekordów do pliku {output_path}")


if __name__ == "__main__":
    main()

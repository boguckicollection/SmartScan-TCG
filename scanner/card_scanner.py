"""Batch scanner for extracting data from card images."""

from pathlib import Path
import re

# Use absolute imports so the script can be executed directly
# or via ``python -m`` without package issues.
from scanner.ocr_engine import extract_text
from scanner.data_exporter import export_to_csv

RARITY_KEYWORDS = [
    "Common",
    "Uncommon",
    "Rare",
    "Ultra Rare",
    "Secret Rare",
    "Promo",
]


def parse_card_text(text: str) -> dict:
    """Parse OCR text and return card attributes."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines else "Unknown"

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
    text = extract_text(str(path))
    return parse_card_text(text)


def scan_directory(dir_path: Path) -> list:
    """Scan all images in the given directory."""
    results = []
    for img_path in sorted(Path(dir_path).glob("*.jpg")):
        results.append(scan_image(img_path))
    for img_path in sorted(Path(dir_path).glob("*.png")):
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

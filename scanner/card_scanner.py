"""Batch scanner for extracting data from card images."""

from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import re
import sys

# Allow running the script directly from the ``scanner`` directory
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use absolute imports so the script can be executed directly
# or via ``python -m`` without package issues.
from scanner.ocr_engine import extract_text
from PIL import Image
from scanner.data_exporter import export_to_csv
from unidecode import unidecode


FORBIDDEN_WORDS = [
    "trainer",
    "supporter",
    "basic",
    "evolves from",
    "stage1",
    "stage2",
    "stage3",
]

SUFFIXES = ["V", "EX", "VMAX", "VSTAR", "GX"]


def clean_name(name: str) -> str:
    """Return a simplified card name for consistent comparison."""
    name = unidecode(name)
    name = re.sub(r"[^a-zA-Z0-9 .]", "", name)
    return name.strip()


def is_valid_name_line(line: str) -> bool:
    """Check if an OCR line is likely a card name."""
    l = line.lower()
    if any(w in l for w in FORBIDDEN_WORDS):
        return False
    return len(line.strip()) >= 3


def extract_card_name(lines: list[str]) -> str:
    """Return the first valid card name from OCR lines."""
    for line in lines:
        if not is_valid_name_line(line):
            continue
        return clean_name(line)
    return "Unknown"


def enhance_for_ocr(image: Image.Image) -> Image.Image:
    """Improve contrast to help OCR."""
    from PIL import ImageEnhance

    gray = image.convert("L")
    enhancer = ImageEnhance.Contrast(gray)
    return enhancer.enhance(2.0)


def safe_crop(image: Image.Image, bbox: tuple[int, int, int, int]):
    """Crop ``image`` safely, returning ``None`` for invalid boxes."""
    left, top, right, bottom = bbox
    if right <= left or bottom <= top:
        return None
    width, height = image.size
    if left < 0 or top < 0 or right > width or bottom > height:
        return None
    return image.crop(bbox)




def parse_card_text(name_text: str | None, number_text: str | None) -> dict:
    """Parse card name and number from OCR text fragments."""
    name = "Unknown"
    if name_text:
        lines = [line.strip() for line in name_text.splitlines() if line.strip()]
        name = extract_card_name(lines)

    number = ""
    if number_text:
        match = re.search(r"\d+/\d+", number_text)
        number = match.group(0) if match else ""

    return {"Name": name, "Number": number}


def scan_image(path: Path) -> dict:
    """Scan a single image and return parsed data."""
    image = Image.open(path)
    width, height = image.size

    # When the image is already a small, cropped fragment (e.g. prepared
    # name/number snippet) the default bounding boxes cut away most of the
    # text.  In that case just run OCR on the whole image and parse the
    # details from the result.
    if width <= 120 and height <= 120:
        full_text = extract_text(image)
        return parse_card_text(full_text, full_text)

    # Name region - top portion of the card
    name_bbox = (
        0,
        0,
        int(width * 0.8),
        int(height * 0.22),
    )
    name_crop = safe_crop(image, name_bbox)
    name_text = None
    if name_crop:
        name_crop = enhance_for_ocr(name_crop)
        name_text = extract_text(name_crop)

    # Number region - lower left corner
    number_bbox = (
        int(width * 0.05),
        int(height * 0.92),
        int(width * 0.40),
        int(height * 0.985),
    )
    number_crop = safe_crop(image, number_bbox)
    number_text = extract_text(number_crop) if number_crop else None

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

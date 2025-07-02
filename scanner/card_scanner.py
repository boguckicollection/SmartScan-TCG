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
import requests


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

# OCR configuration strings
NAME_OCR_CONFIG = (
    "--psm 6 -c tessedit_char_whitelist="
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'VEXSTAR0123456789"
)
NUMBER_OCR_CONFIG = "--psm 6 -c tessedit_char_whitelist=/0123456789"


def clean_name(name: str) -> str:
    """Return a simplified card name for consistent comparison."""
    name = unidecode(name)
    # Keep only alphanumeric characters and apostrophes
    cleaned = re.sub(r"[^a-zA-Z0-9' ]", " ", name)
    words = cleaned.split()
    blacklist = {
        "trainer",
        "supporter",
        "basic",
        "evolves",
        "from",
        "stage1",
        "stage2",
        "stage3",
    }
    filtered = [w for w in words if w.lower() not in blacklist and not any(c.isdigit() for c in w)]
    return " ".join(filtered) if filtered else "Unknown"


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


def clean_number(text: str) -> str:
    """Extract card number from OCR text.

    Supports standard ``X/Y`` format as well as promo identifiers like
    ``SVP EN 126``.
    """
    if not text:
        return "Unknown"
    match = re.search(r"\d{1,3}/\d{1,3}", text)
    if match:
        return match.group(0)
    promo = PROMO_REGEX.search(text)
    if promo:
        return promo.group(1).strip()
    return "Unknown"


def enhance_for_ocr(image: Image.Image) -> Image.Image:
    """Improve contrast to help OCR."""
    from PIL import ImageEnhance, ImageFilter

    gray = image.convert("L")
    enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
    return enhanced.filter(ImageFilter.SHARPEN)


def safe_crop(image: Image.Image, bbox: tuple[int, int, int, int]):
    """Crop ``image`` safely, returning ``None`` for invalid boxes."""
    left, top, right, bottom = bbox
    if right <= left or bottom <= top:
        return None
    width, height = image.size
    if left < 0 or top < 0 or right > width or bottom > height:
        return None
    return image.crop(bbox)


API_URL = "https://api.tcgdex.net/v2/cards"
API_CARD_URL = "https://api.tcgdex.net/v2/en/cards"

PROMO_REGEX = re.compile(r"\b([A-Z]{2,4}\s?EN?\s?\d{1,4})\b")
PROMO_SETS = {
    "SVP": "svpromos",
    "SWSH": "swshpromos",
    "SM": "smpromos",
    "BW": "bwpromos",
    "XY": "xypromos",
}

# Regex pattern for extracting set name from OCR text, e.g. "Set: Base".
SET_REGEX = re.compile(r"set[:\s]+([A-Za-z0-9 '\-]+)", re.IGNORECASE)


def parse_set(text: str) -> str | None:
    """Return the set name found in OCR ``text`` if any."""
    match = SET_REGEX.search(text)
    if not match:
        return None

    raw = match.group(1).strip()
    from scanner.set_mapping import SET_MAP

    # Normalize using mapping when available.
    return SET_MAP.get(raw.upper(), raw)


def query_tcg_api(name: str | None, number: str | None, set_name: str | None = None) -> dict | None:
    """Query the TCGdex API for card details.

    Parameters
    ----------
    name : str or None
        Name detected via OCR.
    number : str or None
        Card number detected via OCR.
    set_name : str or None, optional
        Additional set identifier.
    """
    params = {}
    if name and name != "Unknown":
        params["name"] = name
    if number:
        params["number"] = number
    if set_name:
        params["set"] = set_name
    if not params:
        return None

    try:
        resp = requests.get(API_URL, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    # ``data`` may be a list or a single card dict.
    card = None
    if isinstance(data, list):
        if data:
            card = data[0]
    elif isinstance(data, dict):
        card = data

    if not isinstance(card, dict):
        return None

    return {
        "Name": card.get("name"),
        "Number": card.get("number"),
        "Set": card.get("set", {}).get("id") if isinstance(card.get("set"), dict) else card.get("set"),
    }


def query_card_by_id(card_id: str) -> dict | None:
    """Query the TCGdex API for a card given its identifier."""
    try:
        resp = requests.get(f"{API_CARD_URL}/{card_id}", timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    return {
        "Name": data.get("name"),
        "Number": data.get("number"),
        "Set": data.get("set", {}).get("id") if isinstance(data.get("set"), dict) else data.get("set"),
    }




def parse_card_text(name_text: str | None, number_text: str | None) -> dict:
    """Parse card name and number from OCR text fragments and query the API."""
    name = "Unknown"
    if name_text:
        lines = [line.strip() for line in name_text.splitlines() if line.strip()]
        name = extract_card_name(lines)

    number = ""
    promo_match = None
    set_name = None
    if number_text:
        number = clean_number(number_text)
        promo_match = PROMO_REGEX.search(number_text)
        set_name = parse_set(number_text)

    result = {"Name": name, "Number": number, "Set": set_name or "Unknown"}

    if promo_match:
        card_id = promo_match.group(1).lower().replace(" ", "-")
        result["Number"] = promo_match.group(1)
        result["Set"] = PROMO_SETS.get(promo_match.group(1).split()[0], "Unknown")
        api_data = query_card_by_id(card_id)
    else:
        api_data = query_tcg_api(name, number)
        if not api_data and set_name:
            api_data = query_tcg_api(None, number, set_name)

    if api_data:
        result.update({k: v for k, v in api_data.items() if v})

    return result


def scan_image(path: Path) -> dict:
    """Scan a single image and return parsed data."""
    image = Image.open(path)
    width, height = image.size

    # When the image is already a small, cropped fragment (e.g. prepared
    # name/number snippet) the default bounding boxes cut away most of the
    # text.  In that case just run OCR on the whole image and parse the
    # details from the result.
    if width <= 120 and height <= 120:
        full_text = extract_text(image, config=NAME_OCR_CONFIG)
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
        name_text = extract_text(name_crop, config=NAME_OCR_CONFIG)

    # Number region - lower left corner
    number_bbox = (
        int(width * 0.05),
        int(height * 0.92),
        int(width * 0.40),
        int(height * 0.985),
    )
    number_crop = safe_crop(image, number_bbox)
    number_text = (
        extract_text(number_crop, config=NUMBER_OCR_CONFIG) if number_crop else None
    )

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

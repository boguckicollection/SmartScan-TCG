"""Batch scanner for extracting data from card images."""

from __future__ import annotations

from pathlib import Path
from collections import defaultdict
from collections.abc import Callable
import re
import sys
from difflib import SequenceMatcher

# Allow running the script directly from the ``scanner`` directory
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use absolute imports so the script can be executed directly
# or via ``python -m`` without package issues.
from scanner.data_exporter import export_to_csv
from scanner.image_analyzer import predict_type
from scanner.classifier import CardClassifier
from PIL import Image
import requests

try:  # optional when torch is not installed
    import torch
    from torchvision import transforms
except Exception:  # pragma: no cover - torch not available during some tests
    torch = None
    transforms = None

EXCLUDED_WORDS = {
    "basic",
    "trainer",
    "supporter",
    "stage1",
    "stage2",
    "stage3",
    "evolves",
    "from",
    "item",
    "stadium",
    "pokemon",
    "hp",
    "ex",
    "gx",
    "vmax",
    "vstar",
}


FORBIDDEN_WORDS = [
    "trainer",
    "supporter",
    "basic",
    "evolves from",
    "stage1",
    "stage 1",
    "stage2",
    "stage 2",
    "stage3",
    "stage 3",
]

SUFFIXES = ["V", "EX", "VMAX", "VSTAR", "GX"]

# OCR configuration strings
NAME_OCR_CONFIG = (
    "--psm 7 -c tessedit_char_whitelist="
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'VEXSTAR0123456789"
)
NUMBER_OCR_CONFIG = "--psm 6 -c tessedit_char_whitelist=/0123456789"


def clean_card_name(text: str) -> str:
    """Return ``text`` cleaned of unwanted tokens."""
    if not text:
        return "Unknown"
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    tokens = [
        w.capitalize()
        for w in text.split()
        if w not in EXCLUDED_WORDS and not w.isdigit()
    ]
    return " ".join(tokens) if tokens else "Unknown"


def is_valid_name_line(line: str) -> bool:
    """Check if an OCR line is likely a card name."""
    l = line.lower()
    if any(w in l for w in FORBIDDEN_WORDS):
        return False
    if any(ch.isdigit() for ch in l):
        return False
    return len(line.strip()) >= 3


def extract_card_name(lines: list[str]) -> str:
    """Return the most likely card name from OCR lines."""
    best = ""
    for line in lines:
        if not is_valid_name_line(line):
            continue
        cleaned = clean_card_name(line)
        if len(cleaned) > len(best):
            best = cleaned
    return best or "Unknown"


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


def extract_number_total(text: str) -> tuple[str | None, str | None]:
    """Return card number and set total if present in ``text``."""
    if not text:
        return None, None
    match = NUMBER_TOTAL_REGEX.search(text)
    if not match:
        return None, None
    return match.group(1), match.group(2)


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


API_BASE_URL = "https://api.tcgdex.net/v2"
SET_LIST_URL = f"{API_BASE_URL}/en/sets"
CARD_URL_TEMPLATE = f"{API_BASE_URL}/en/cards/{{set_id}}-{{card_number}}"

PROMO_REGEX = re.compile(r"\b([A-Z]{2,4}\s?EN?\s?\d{1,4})\b")
PROMO_SETS = {
    "SVP": "svpromos",
    "SWSH": "swshpromos",
    "SM": "smpromos",
    "BW": "bwpromos",
    "XY": "xypromos",
}

# ---------------------------------------------------------------------------
# Language detection utilities
# ---------------------------------------------------------------------------

def detect_language(text: str | None) -> str:
    """Return ISO language code guessed from ``text``."""
    if not text:
        return "en"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh-hans"
    if re.search(r"[ぁ-んァ-ン]", text):
        return "ja"
    if re.search(r"\d{2}\s+\d{2}/\d{2}", text):
        # Common pattern on Chinese/Japanese promos
        return "zh-hans"
    if re.search(r"PROMO|SVP", text, re.IGNORECASE):
        return "en"
    return "en"


def fix_merged_number(text: str) -> str:
    """Return ``text`` with typical OCR merge errors corrected."""
    normalized = text.replace(" ", "")
    match = re.match(r"(\d{2})(\d{2}/\d{2})", normalized)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    match = re.match(r"(\d)(\d{2}/\d{2})", normalized)
    if match:
        return f"0{match.group(1)} {match.group(2)}"
    return text


def fix_card_number(number: str) -> str:
    """Return ``number`` with simple merged prefix errors corrected."""
    if re.match(r"^\d{3}/\d{2}$", number):
        return f"{number[:2]} {number[2:]}"
    return number


def extract_promo_card_id(text: str) -> str | None:
    """Return promo card identifier found in ``text`` if any."""
    fixed = fix_merged_number(text)
    match = re.search(r"(\d{2})\s*\d{2}/\d{2}", fixed)
    if match:
        return f"ccp-{match.group(1)}"
    return None

# Regex pattern for extracting ``number/total`` from OCR text.
NUMBER_TOTAL_REGEX = re.compile(r"(\d{1,3})\/(\d{1,3})")

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


def query_tcg_api(
    name: str | None,
    number: str | None,
    set_name: str | None = None,
    lang: str = "en",
) -> dict | None:
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

    try:
        url = f"{API_BASE_URL}/{lang}/cards"
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        if not data or "cards" not in data or not data["cards"]:
            print(f"[API] No results for params: {params}")
            return None

        card = data["cards"][0]
        return {
            "Name": card.get("name"),
            "Number": card.get("number"),
            "Set": card.get("set", {}).get("id") if isinstance(card.get("set"), dict) else card.get("set"),
        }
    except Exception as e:
        print(f"[API] Error: {e} for params: {params}")
        return None


def query_card_by_id(card_id: str, lang: str = "en") -> dict | None:
    """Query the TCGdex API for a card given its identifier."""
    try:
        url = f"{API_BASE_URL}/{lang}/cards/{card_id}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except requests.HTTPError as e:
        print(f"[API ID ERROR] {e}")
        return None
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    return {
        "Name": data.get("name"),
        "Number": data.get("number"),
        "Set": data.get("set", {}).get("id") if isinstance(data.get("set"), dict) else data.get("set"),
    }


def is_similar(a: str, b: str, threshold: float = 0.7) -> bool:
    """Return ``True`` if two strings are similar enough."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold


def lookup_card_by_number_and_total(card_number: str, set_total: str, approx_name: str = "") -> dict | None:
    """Return card details by number and set size with optional fuzzy name."""
    try:
        resp = requests.get(SET_LIST_URL, timeout=10)
        resp.raise_for_status()
        all_sets = resp.json()
    except Exception as exc:
        print(f"[TCGdex] Error loading sets: {exc}")
        return None

    candidates = [s["id"] for s in all_sets if str(s.get("total")) == str(set_total)]
    print(f"[DEBUG] Candidate sets for total {set_total}: {candidates}")

    matches: list[dict] = []
    for set_id in candidates:
        url = CARD_URL_TEMPLATE.format(set_id=set_id, card_number=card_number)
        try:
            card_resp = requests.get(url, timeout=5)
            if card_resp.status_code == 200:
                card = card_resp.json()
                api_name = card.get("name", "")
                if approx_name and is_similar(approx_name, api_name):
                    print(f"[MATCH] Found close name match: {api_name} in set {set_id}")
                    return {"Name": api_name, "Number": card.get("number"), "Set": set_id}
                matches.append({"Name": api_name, "Number": card.get("number"), "Set": set_id})
        except Exception as exc:
            print(f"[WARN] Failed to get card {set_id}-{card_number}: {exc}")
            continue

    if len(matches) == 1:
        m = matches[0]
        print(f"[FALLBACK] Only one possible match: {m['Name']} from {m['Set']}")
        return m

    print(f"[FAIL] No reliable match for {card_number}/{set_total} with name '{approx_name}'")
    return None




def parse_card_text(
    name_text: str | None,
    number_text: str | None,
    cleaned_name: str | None = None,
) -> dict:
    """Parse card name and number from OCR text fragments and query the API."""
    full_text = (name_text or "") + "\n" + (number_text or "")
    lang = detect_language(full_text)
    print(f"[LANG DETECTED] {lang}")

    promo_id = extract_promo_card_id(full_text)
    api_data = None
    if promo_id:
        print(f"[PROMO] Detected promo card ID: {promo_id}, lang: {lang}")
        print(f"[OCR RAW NUMBER] {number_text}")
        print(f"[OCR FIXED PROMO ID] {promo_id}")
        api_data = query_card_by_id(promo_id, lang)

    raw_name = name_text.strip() if name_text else "Unknown"
    cleaned = cleaned_name if cleaned_name is not None else clean_card_name(raw_name)
    print(f"[DEBUG] OCR raw name: '{raw_name}' → Cleaned: '{cleaned}'")
    if len(cleaned) < 3:
        cleaned = "Unknown"
    name = cleaned

    number = ""
    promo_match = None
    set_name = None
    card_num = None
    total = None
    if number_text:
        number = clean_number(number_text)
        number = fix_card_number(number)
        promo_match = PROMO_REGEX.search(number_text)
        set_name = parse_set(number_text)
        card_num, total = extract_number_total(number_text)

    result = {"Name": name, "Number": number, "Set": set_name or "Unknown"}

    if api_data is None:
        if promo_match:
            card_id = promo_match.group(1).lower().replace(" ", "-")
            result["Number"] = promo_match.group(1)
            result["Set"] = PROMO_SETS.get(promo_match.group(1).split()[0], "Unknown")
            api_data = query_card_by_id(card_id, lang)
        elif lang == "zh-hans" and number_text:
            id_match = re.search(r"(\d{2})\s+\d{2}/\d{2}", number_text)
            if id_match:
                card_id = f"ccp-{id_match.group(1)}"
                api_data = query_card_by_id(card_id, lang)
            else:
                api_data = query_tcg_api(name, number, lang=lang)
        else:
            api_data = query_tcg_api(name, number, lang=lang)
            if not api_data and number:
                print(f"[API fallback] Retrying with only number: {number}")
                api_data = query_tcg_api(None, number, lang=lang)
            if not api_data and set_name:
                api_data = query_tcg_api(None, number, set_name, lang=lang)
            if not api_data and card_num and total:
                approx = name if name != "Unknown" else ""
                api_data = lookup_card_by_number_and_total(card_num, total, approx)

    if api_data:
        result.update({k: v for k, v in api_data.items() if v})

    return result


CARD_MODEL_PATH = Path(__file__).resolve().parent / "card_model.pt"
_card_clf: CardClassifier | None = None


def predict_card_id(image_path: str, model_path: str | Path = CARD_MODEL_PATH) -> str:
    """Return predicted card identifier for ``image_path``."""
    if not torch:
        raise ImportError("PyTorch is required for prediction")
    global _card_clf
    if _card_clf is None:
        if not Path(model_path).exists():
            raise RuntimeError("Card classifier model not found")
        _card_clf = CardClassifier.load(model_path, device="cpu")
    transform = transforms.Compose([transforms.Resize((64, 64)), transforms.ToTensor()])
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img)
    return _card_clf.predict([tensor])[0]


def scan_image(path: Path) -> dict:
    """Scan a single image and return predicted data."""
    card_id = predict_card_id(str(path))
    try:
        card_type = predict_type(str(path))
    except Exception:  # pragma: no cover - prediction may fail in tests
        card_type = "common"

    api_data = query_card_by_id(card_id)

    result = {
        "CardID": card_id,
        "Name": "Unknown",
        "Number": "",
        "Set": "Unknown",
        "Type": card_type,
        "ImagePath": str(path),
    }
    if api_data:
        result.update({k: v for k, v in api_data.items() if v})
    else:
        if "-" in card_id:
            set_id, number = card_id.split("-", 1)
            result["Set"] = set_id
            result["Number"] = number
    return result


def scan_directory(dir_path: Path) -> list:
    """Scan all images in the given directory."""
    results = []
    for ext in ("*.jpg", "*.png"):
        for img_path in sorted(Path(dir_path).glob(ext)):
            results.append(scan_image(img_path))
    return results


def scan_files(
    files: list[Path],
    progress_callback: Callable[[int, int], None] | None = None,
) -> list:
    """Scan a list of image paths.

    Parameters
    ----------
    files : list[Path]
        Images to process.
    progress_callback : callable, optional
        Function called with the current index and total after each file.
    """
    results = []
    total = len(files)
    for idx, img_path in enumerate(files, 1):
        results.append(scan_image(img_path))
        if progress_callback:
            progress_callback(idx, total)
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

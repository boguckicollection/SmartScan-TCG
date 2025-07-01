"""OCR and text analysis utilities."""

import os
import pytesseract
from PIL import Image

# Allow overriding the Tesseract executable path via environment variable.
tesseract_cmd = os.getenv("TESSERACT_CMD") or os.getenv("TESSERACT_PATH")
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def extract_text(image_path: str) -> str:
    """Return raw text from an image."""
    image = Image.open(image_path)
    try:
        return pytesseract.image_to_string(image)
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract executable not found. Install Tesseract and add it to your PATH "
            "or set the TESSERACT_CMD environment variable."
        ) from exc

"""OCR and text analysis utilities."""

import pytesseract
from PIL import Image


def extract_text(image_path: str) -> str:
    """Return raw text from an image."""
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)

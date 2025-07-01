import os
import pytesseract
from PIL import Image

# Allow overriding the Tesseract executable path via environment variable.
tesseract_cmd = os.getenv("TESSERACT_CMD") or os.getenv("TESSERACT_PATH")
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def extract_text(image: Image.Image) -> str:
    """Return raw text from a PIL image."""
    try:
        return pytesseract.image_to_string(image, config="--psm 7")
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract executable not found. Install Tesseract and add it to your PATH "
            "or set the TESSERACT_CMD environment variable."
        ) from exc

"""OCR and text analysis utilities."""

import os
import pytesseract
from PIL import Image

# Allow overriding the Tesseract executable path via environment variable.
tesseract_cmd = os.getenv("TESSERACT_CMD") or os.getenv("TESSERACT_PATH")
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def extract_text(image_path: str, bbox=None) -> str:
    """Return raw text from an image.

    Parameters
    ----------
    image_path : str
        Path to the source image.
    bbox : tuple, optional
        ``(left, upper, right, lower)`` bounding box. If provided, the image is
        cropped to this area before OCR is performed.
    """
    image = Image.open(image_path)
    if bbox:
        image = image.crop(bbox)
    try:
        return pytesseract.image_to_string(image, config="--psm 7")
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract executable not found. Install Tesseract and add it to your PATH "
            "or set the TESSERACT_CMD environment variable."
        ) from exc

"""Image processing helpers for detecting card characteristics."""

from PIL import Image


def analyze_image(path: str) -> dict:
    """Return extracted features from card image."""
    image = Image.open(path)
    # Placeholder logic
    return {"holo": False, "reverse": False, "rarity": "common"}

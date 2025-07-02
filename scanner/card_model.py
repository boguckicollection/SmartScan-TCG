"""Utilities for loading and using the card identification model."""

from __future__ import annotations

from pathlib import Path
from PIL import Image

try:
    import torch
    from torchvision import transforms
except Exception:  # pragma: no cover - torch may be missing
    torch = None
    transforms = None

from .classifier import CardClassifier

MODEL_PATH = Path(__file__).resolve().parent / "card_model.pt"

_model: CardClassifier | None = None


def load(model_path: str | Path = MODEL_PATH) -> CardClassifier:
    """Return a loaded :class:`CardClassifier` from ``model_path``."""
    if not torch:
        raise ImportError("PyTorch is required for prediction")
    global _model
    if _model is None:
        if not Path(model_path).exists():
            raise RuntimeError("Card classifier model not found")
        _model = CardClassifier.load(model_path, device="cpu")
    return _model


def predict(image_path: str, model_path: str | Path = MODEL_PATH) -> str:
    """Return predicted card identifier for ``image_path``."""
    clf = load(model_path)
    transform = transforms.Compose([transforms.Resize((64, 64)), transforms.ToTensor()])
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img)
    return clf.predict([tensor])[0]

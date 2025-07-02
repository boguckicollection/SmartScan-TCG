"""Utilities for training and using the card type classifier."""

from __future__ import annotations

from pathlib import Path
import csv
from PIL import Image

try:
    import torch
    from torchvision import transforms
except Exception:  # pragma: no cover - torch may be missing
    torch = None
    transforms = None

from .classifier import CardClassifier

DATASET_PATH = Path(__file__).resolve().parent / "dataset.csv"
MODEL_PATH = Path(__file__).resolve().parent / "type_model.pt"

_model: CardClassifier | None = None


def _load_dataset(csv_path: str | Path) -> tuple[list[torch.Tensor], list[str]]:
    """Return tensors and labels from ``csv_path``."""
    if not torch:
        raise ImportError("PyTorch is required for training")
    images: list[torch.Tensor] = []
    labels: list[str] = []

    transform = transforms.Compose([transforms.Resize((64, 64)), transforms.ToTensor()])
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            img = Image.open(row["image_path"]).convert("RGB")
            images.append(transform(img))
            label = "common"
            if str(row.get("holo", "")).lower() in {"1", "true", "t"}:
                label = "holo"
            elif str(row.get("reverse", "")).lower() in {"1", "true", "t"}:
                label = "reverse"
            labels.append(label)
    return images, labels


def train_type_classifier(
    csv_path: str | Path = DATASET_PATH,
    model_path: str | Path = MODEL_PATH,
    epochs: int = 1,
) -> CardClassifier:
    """Train the type classifier from labeled data and save to ``model_path``."""
    if not torch:
        raise ImportError("PyTorch is required for training")

    images, labels = _load_dataset(csv_path)
    clf = CardClassifier(num_classes=3, model_name="mobilenet", device="cpu")
    clf.fit(images, labels, epochs=max(1, epochs))
    clf.save(model_path)
    global _model
    _model = clf
    return clf


def _ensure_loaded(model_path: str | Path = MODEL_PATH) -> CardClassifier:
    """Load the classifier if not already loaded."""
    global _model
    if _model is None:
        if not Path(model_path).exists():
            raise RuntimeError("Type classifier model not found")
        _model = CardClassifier.load(model_path, device="cpu")
    return _model


def predict_type(image_path: str, model_path: str | Path = MODEL_PATH) -> str:
    """Return predicted card type: ``holo``, ``reverse``, or ``common``."""
    if not torch:
        raise ImportError("PyTorch is required for prediction")
    clf = _ensure_loaded(model_path)
    transform = transforms.Compose([transforms.Resize((64, 64)), transforms.ToTensor()])
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img)
    return clf.predict([tensor])[0]

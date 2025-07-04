"""Utilities for training and using the card type classifier."""

from __future__ import annotations

from scanner.classifier import CardClassifier
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from pathlib import Path
import torch
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


def train_type_classifier(dataset_dir: Path, output_model_path: Path):
    """Train a model to classify card types (e.g. common, holo, reverse)."""
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
    ])
    dataset = datasets.ImageFolder(dataset_dir, transform=transform)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)

    X, y = [], []
    for img, label in loader:
        for i in range(img.size(0)):
            X.append(img[i])
            y.append(dataset.classes[label[i]])

    clf = CardClassifier(model_name="resnet18", num_classes=len(set(y)))
    clf.fit(X, y, epochs=5)
    clf.save(output_model_path)
    print(f"[OK] Model zapisany do {output_model_path}")


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

if __name__ == "__main__":
    dataset_path = Path("data/type_dataset")
    output_path = Path(__file__).resolve().parent / "type_model.pt"
    train_type_classifier(dataset_path, output_path)
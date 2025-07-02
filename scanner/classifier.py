"""CNN-based card classifier using PyTorch."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from sklearn.base import BaseEstimator

try:
    import torch
    from torch import nn
    from torchvision import models
except Exception:  # pragma: no cover - torch may be missing when tests run
    torch = None
    nn = None
    models = None


class CardClassifier(BaseEstimator):
    """Image classifier for predicting card IDs."""

    def __init__(self, model_name: str = "resnet18", num_classes: int | None = None, device: str | None = None):
        self.model_name = model_name
        self.num_classes = num_classes
        self.device = device or ("cuda" if torch and torch.cuda.is_available() else "cpu")
        self.classes_: List[str] = []
        self.model: nn.Module | None = None
        if torch:
            self._build_model()

    # ------------------------------------------------------------------
    def _build_model(self) -> None:
        if not torch:
            return
        name = self.model_name.lower()
        if name == "mobilenet":
            self.model = models.mobilenet_v2(weights=None)
            in_features = self.model.classifier[1].in_features
            self.model.classifier[1] = nn.Linear(in_features, self.num_classes or 1)
        elif name == "efficientnet":
            self.model = models.efficientnet_b0(weights=None)
            in_features = self.model.classifier[1].in_features
            self.model.classifier[1] = nn.Linear(in_features, self.num_classes or 1)
        else:
            self.model = models.resnet18(weights=None)
            in_features = self.model.fc.in_features
            self.model.fc = nn.Linear(in_features, self.num_classes or 1)
        self.model.to(self.device)

    # ------------------------------------------------------------------
    def fit(self, X: Iterable[torch.Tensor], y: Iterable[str], epochs: int = 1, lr: float = 1e-3, batch_size: int = 32):
        """Train the classifier on tensors ``X`` with labels ``y``."""
        if not torch:
            raise ImportError("PyTorch is required for training")

        self.classes_ = sorted({str(label) for label in y})
        cls_to_idx = {c: i for i, c in enumerate(self.classes_)}
        targets = [cls_to_idx[str(label)] for label in y]

        if self.model is None or (self.num_classes != len(self.classes_)):
            self.num_classes = len(self.classes_)
            self._build_model()

        dataset = torch.utils.data.TensorDataset(torch.stack(list(X)), torch.tensor(targets))
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

        self.model.train()
        for _ in range(max(1, epochs)):
            for images, labels in loader:
                images = images.to(self.device)
                labels = labels.to(self.device)
                optimizer.zero_grad()
                output = self.model(images)
                loss = criterion(output, labels)
                loss.backward()
                optimizer.step()
        return self

    # ------------------------------------------------------------------
    def predict(self, X: Iterable[torch.Tensor]) -> List[str]:
        """Return predicted card IDs for tensors ``X``."""
        if not torch:
            raise ImportError("PyTorch is required for prediction")
        if not self.classes_:
            raise RuntimeError("Model has not been fitted")
        self.model.eval()
        with torch.no_grad():
            images = torch.stack(list(X)).to(self.device)
            output = self.model(images)
            idxs = output.argmax(dim=1).cpu().tolist()
        return [self.classes_[i] for i in idxs]

    # ------------------------------------------------------------------
    def save(self, path: str | Path) -> None:
        """Save model weights and metadata to ``path``."""
        if not torch:
            raise ImportError("PyTorch is required to save the model")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "model_state": self.model.state_dict() if self.model else None,
                "classes": self.classes_,
                "model_name": self.model_name,
                "num_classes": self.num_classes,
            },
            str(path),
        )

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, path: str | Path, device: str | None = None) -> "CardClassifier":
        """Load classifier from ``path``."""
        if not torch:
            raise ImportError("PyTorch is required to load the model")
        data = torch.load(str(path), map_location=device or ("cuda" if torch.cuda.is_available() else "cpu"))
        obj = cls(data.get("model_name", "resnet18"), data.get("num_classes"), device=device)
        obj.classes_ = data.get("classes", [])
        if obj.model:
            obj.model.load_state_dict(data.get("model_state", {}))
        return obj


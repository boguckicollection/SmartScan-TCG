import types
from pathlib import Path

import scanner.image_analyzer as ia


def test_train_and_predict(tmp_path, monkeypatch):
    img = tmp_path / "img.jpg"
    img.write_text("dummy")
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("image_path,holo,reverse\n" + f"{img},1,0\n")

    class DummyClassifier:
        def __init__(self, *a, **kw):
            pass

        def fit(self, X, y, epochs=1, lr=1e-3, batch_size=32):
            self.trained = True
            return self

        def predict(self, X):
            return ["holo" for _ in X]

        def save(self, path):
            Path(path).write_text("model")

        @classmethod
        def load(cls, path, device=None):
            return cls()

    monkeypatch.setattr(ia, "CardClassifier", DummyClassifier)
    monkeypatch.setattr(ia, "torch", types.SimpleNamespace())
    monkeypatch.setattr(
        ia,
        "transforms",
        types.SimpleNamespace(
            Compose=lambda x: (lambda img: img),
            Resize=lambda *a, **k: None,
            ToTensor=lambda: None,
        ),
    )
    class DummyImage:
        def convert(self, mode):
            return self

    monkeypatch.setattr(ia.Image, "open", lambda p: DummyImage())

    ia.train_type_classifier(csv_path, tmp_path / "model.pt", epochs=1)
    pred = ia.predict_type(str(img), tmp_path / "model.pt")
    assert pred == "holo"

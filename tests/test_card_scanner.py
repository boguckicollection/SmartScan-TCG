from pathlib import Path
import types
import sys


class StubImage:
    def __init__(self, size=(100, 100)):
        self.size = size

    @classmethod
    def new(cls, mode, size, color=None):
        return cls(size)

    @classmethod
    def open(cls, path):
        return cls()

    def save(self, path):
        with open(path, "wb") as fh:
            fh.write(b"")


PIL_image_module = types.SimpleNamespace(Image=StubImage, new=StubImage.new, open=StubImage.open)
sys.modules.setdefault("PIL.Image", PIL_image_module)
sys.modules.setdefault("PIL", types.SimpleNamespace(Image=PIL_image_module))
Image = StubImage

# Stub modules that may be missing
sys.modules.setdefault("requests", types.SimpleNamespace(get=lambda *a, **k: None))

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scanner.card_scanner as card_scanner


def create_dummy_image(path: Path, size=(100, 100)) -> None:
    Image.new("RGB", size, color="white").save(path)


def test_scan_image_with_api(tmp_path, monkeypatch):
    img = tmp_path / "img.jpg"
    create_dummy_image(img)

    monkeypatch.setattr(card_scanner, "predict_card_id", lambda p: "base-1/102")
    monkeypatch.setattr(card_scanner, "predict_type", lambda p: "holo")

    captured = {}

    def fake_query(card_id, lang="en"):
        captured["id"] = card_id
        return {"Name": "Pikachu", "Number": "1/102", "Set": "Base"}

    monkeypatch.setattr(card_scanner, "query_card_by_id", fake_query)

    data = card_scanner.scan_image(img)

    assert captured["id"] == "base-1/102"
    assert data["Name"] == "Pikachu"
    assert data["Number"] == "1/102"
    assert data["Set"] == "Base"
    assert data["Type"] == "holo"
    assert data["ImagePath"] == str(img)


def test_scan_image_fallback(tmp_path, monkeypatch):
    img = tmp_path / "img.jpg"
    create_dummy_image(img)

    monkeypatch.setattr(card_scanner, "predict_card_id", lambda p: "base-2")
    monkeypatch.setattr(card_scanner, "predict_type", lambda p: "common")
    monkeypatch.setattr(card_scanner, "query_card_by_id", lambda *a, **k: None)

    data = card_scanner.scan_image(img)

    assert data["Name"] == "Unknown"
    assert data["Number"] == "2"
    assert data["Set"] == "base"
    assert data["Type"] == "common"


def test_export_to_csv(tmp_path):
    rows = [
        {"Name": "Test", "Number": "1/1", "Ilość": 2},
        {"Name": "Foo", "Number": "2/2", "Ilość": 1},
    ]
    out_file = tmp_path / "out.csv"
    card_scanner.export_to_csv(rows, str(out_file))
    assert out_file.exists()
    text = out_file.read_text()
    assert "Name" in text
    assert "Test" in text

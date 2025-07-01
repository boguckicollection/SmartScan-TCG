from pathlib import Path

import types
import sys
import pytest


class StubImage:
    def __init__(self, size=(100, 100)):
        self.size = size

    @classmethod
    def new(cls, mode, size, color=None):
        return cls(size)

    @classmethod
    def open(cls, path):
        return cls()

    def crop(self, bbox):
        w = max(0, bbox[2] - bbox[0])
        h = max(0, bbox[3] - bbox[1])
        return StubImage((w, h))

    def save(self, path):
        with open(path, "wb") as f:
            f.write(b"")


sys.modules.setdefault("PIL", types.SimpleNamespace(Image=StubImage))
Image = StubImage
sys.modules.setdefault(
    "pytesseract",
    types.SimpleNamespace(
        pytesseract=types.SimpleNamespace(
            TesseractNotFoundError=RuntimeError,
            tesseract_cmd="",
        ),
        image_to_string=lambda *args, **kwargs: "",
    ),
)


class DummyDataFrame:
    def __init__(self, data):
        pass

    def to_csv(self, path, index=False):
        with open(path, "w") as f:
            f.write("")


sys.modules.setdefault("pandas", types.SimpleNamespace(DataFrame=DummyDataFrame))

sys.modules.setdefault("unidecode", types.SimpleNamespace(unidecode=lambda s: s))

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scanner.card_scanner as card_scanner


def create_dummy_image(path: Path, size=(100, 100)) -> None:
    Image.new("RGB", size, color="white").save(path)


def test_scan_image_fallback(tmp_path, monkeypatch):
    img_path = tmp_path / "test.jpg"
    # Larger image emulates a full card requiring bounding boxes
    create_dummy_image(img_path, size=(200, 300))
    monkeypatch.setattr(card_scanner.Image, "open", classmethod(lambda cls, p: card_scanner.Image(size=(200, 300))))

    calls = []

    def fake_extract_text(path, bbox=None):
        calls.append((path, bbox))
        if bbox is not None:
            raise TypeError("unexpected keyword")
        return "Name\nSet: Base\n1/102"

    monkeypatch.setattr(card_scanner, "extract_text", fake_extract_text)

    data = card_scanner.scan_image(img_path)

    assert data["Name"] == "Name"
    assert data["Number"] == "1/102"
    # Each OCR region triggers a fallback, so four calls total
    assert len(calls) == 4
    assert calls[1][1] is None
    assert calls[3][1] is None
    # Temporary files should be used for fallback calls
    assert Path(calls[1][0]) != img_path
    assert not Path(calls[1][0]).exists()
    assert Path(calls[3][0]) != img_path
    assert not Path(calls[3][0]).exists()


def test_scan_image_precropped(tmp_path, monkeypatch):
    img_path = tmp_path / "precrop.jpg"
    # Small square image triggers the precropped path
    create_dummy_image(img_path, size=(100, 100))
    monkeypatch.setattr(card_scanner.Image, "open", classmethod(lambda cls, p: card_scanner.Image(size=(100, 100))))
    calls = []

    def fake_extract_text(path, bbox=None):
        calls.append((path, bbox))
        return "Name\n1/102"

    monkeypatch.setattr(card_scanner, "extract_text", fake_extract_text)

    data = card_scanner.scan_image(img_path)

    assert data["Name"] == "Name"
    assert data["Number"] == "1/102"
    # Only one OCR call should be made on the entire image
    assert calls == [(str(img_path), None)]


def test_export_to_csv(tmp_path):
    rows = [
        {"Name": "Test", "Number": "1/1", "Ilość": 2},
        {"Name": "Foo", "Number": "2/2", "Ilość": 1},
    ]
    out_file = tmp_path / "out.csv"
    card_scanner.export_to_csv(rows, str(out_file))
    assert out_file.exists()
    content = out_file.read_text()
    assert "Name" in content
    assert "Test" in content

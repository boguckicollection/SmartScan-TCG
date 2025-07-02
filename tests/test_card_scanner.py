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


PIL_image_module = types.SimpleNamespace(Image=StubImage, new=StubImage.new, open=StubImage.open)
sys.modules.setdefault("PIL.Image", PIL_image_module)
sys.modules.setdefault("PIL", types.SimpleNamespace(Image=PIL_image_module))
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
sys.modules.setdefault("requests", types.SimpleNamespace(get=lambda *a, **k: None))

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scanner.card_scanner as card_scanner


def create_dummy_image(path: Path, size=(100, 100)) -> None:
    Image.new("RGB", size, color="white").save(path)


def test_scan_image_regions(tmp_path, monkeypatch):
    img_path = tmp_path / "test.jpg"
    # Larger image emulates a full card requiring bounding boxes
    create_dummy_image(img_path, size=(200, 300))
    monkeypatch.setattr(card_scanner.Image, "open", lambda p: card_scanner.Image.Image(size=(200, 300)))

    ocr_calls = []

    def fake_extract_text(image, config=None):
        ocr_calls.append(image.size)
        if image.size == (160, 66):
            return "Name"
        return "Set: Base\n1/102"

    monkeypatch.setattr(card_scanner, "extract_text", fake_extract_text)
    monkeypatch.setattr(card_scanner, "enhance_for_ocr", lambda img: img)
    monkeypatch.setattr(card_scanner, "query_tcg_api", lambda *args, **kwargs: None)

    data = card_scanner.scan_image(img_path)

    assert data["Name"] == "Name"
    assert data["Number"] == "1/102"
    assert ocr_calls == [(160, 66), (70, 19)]


def test_scan_image_precropped(tmp_path, monkeypatch):
    img_path = tmp_path / "precrop.jpg"
    # Small square image triggers the precropped path
    create_dummy_image(img_path, size=(100, 100))
    monkeypatch.setattr(card_scanner.Image, "open", lambda p: card_scanner.Image.Image(size=(100, 100)))
    ocr_calls = []

    def fake_extract_text(image, config=None):
        ocr_calls.append(image.size)
        return "Name\n1/102"

    monkeypatch.setattr(card_scanner, "extract_text", fake_extract_text)
    monkeypatch.setattr(card_scanner, "enhance_for_ocr", lambda img: img)
    monkeypatch.setattr(card_scanner, "query_tcg_api", lambda *args, **kwargs: None)

    data = card_scanner.scan_image(img_path)

    assert data["Name"] == "Name"
    assert data["Number"] == "1/102"
    # Only one OCR call should be made on the entire image
    assert ocr_calls == [(100, 100)]


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


def test_scan_image_api_override(tmp_path, monkeypatch):
    img_path = tmp_path / "api.jpg"
    create_dummy_image(img_path, size=(100, 100))
    monkeypatch.setattr(card_scanner.Image, "open", lambda p: card_scanner.Image.Image(size=(100, 100)))

    monkeypatch.setattr(card_scanner, "extract_text", lambda *args, **kw: "Name\n1/102")
    monkeypatch.setattr(card_scanner, "enhance_for_ocr", lambda img: img)

    def fake_api(name, number, set_name=None):
        return {"Name": "Exact Name", "Number": "1/102", "Set": "Base"}

    monkeypatch.setattr(card_scanner, "query_tcg_api", fake_api)

    data = card_scanner.scan_image(img_path)

    assert data["Name"] == "Exact Name"
    assert data["Number"] == "1/102"
    assert data["Set"] == "Base"


def test_scan_image_promo_number(tmp_path, monkeypatch):
    img_path = tmp_path / "promo.jpg"
    create_dummy_image(img_path, size=(100, 100))
    monkeypatch.setattr(card_scanner.Image, "open", lambda p: card_scanner.Image.Image(size=(100, 100)))

    monkeypatch.setattr(card_scanner, "extract_text", lambda *a, **kw: "Name\nSVP EN 126")
    monkeypatch.setattr(card_scanner, "enhance_for_ocr", lambda img: img)

    captured = {}

    def fake_query_card(card_id):
        captured["id"] = card_id
        return {"Name": "Promo", "Number": "SVP EN 126", "Set": "svpromos"}

    monkeypatch.setattr(card_scanner, "query_card_by_id", fake_query_card)
    monkeypatch.setattr(card_scanner, "query_tcg_api", lambda *a, **kw: None)

    data = card_scanner.scan_image(img_path)

    assert captured.get("id") == "svp-en-126"
    assert data["Name"] == "Promo"
    assert data["Number"] == "SVP EN 126"
    assert data["Set"] == "svpromos"


def test_lookup_with_number_and_set(tmp_path, monkeypatch):
    img_path = tmp_path / "lookup.jpg"
    create_dummy_image(img_path, size=(200, 300))
    monkeypatch.setattr(card_scanner.Image, "open", lambda p: card_scanner.Image.Image(size=(200, 300)))

    ocr_calls = []

    def fake_extract_text(image, config=None):
        ocr_calls.append(image.size)
        if image.size == (160, 66):
            return "Wrong Name"
        return "Set: Base\n1/102"

    monkeypatch.setattr(card_scanner, "extract_text", fake_extract_text)
    monkeypatch.setattr(card_scanner, "enhance_for_ocr", lambda img: img)

    api_calls = []

    def fake_api(name, number, set_name=None):
        api_calls.append({"name": name, "number": number, "set": set_name})
        if len(api_calls) == 1:
            return None
        return {"Name": "Pikachu", "Number": number, "Set": set_name}

    monkeypatch.setattr(card_scanner, "query_tcg_api", fake_api)

    data = card_scanner.scan_image(img_path)

    assert api_calls == [
        {"name": "Wrong Name", "number": "1/102", "set": None},
        {"name": None, "number": "1/102", "set": "Base"},
    ]
    assert data["Name"] == "Pikachu"
    assert data["Set"] == "Base"

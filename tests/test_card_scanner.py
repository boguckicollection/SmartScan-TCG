from pathlib import Path

from PIL import Image
import pytest

import scanner.card_scanner as card_scanner


def create_dummy_image(path: Path) -> None:
    Image.new("RGB", (100, 100), color="white").save(path)


def test_scan_image_fallback(tmp_path, monkeypatch):
    img_path = tmp_path / "test.jpg"
    create_dummy_image(img_path)

    calls = []

    def fake_extract_text(path, bbox=None):
        calls.append((path, bbox))
        if bbox is not None:
            raise TypeError("unexpected keyword")
        return "Name\nSet: Base\n1/102"

    monkeypatch.setattr(card_scanner, "extract_text", fake_extract_text)

    data = card_scanner.scan_image(img_path)

    assert data["Name"] == "Name"
    assert data["Set"] == "Base"
    assert data["Number"] == "1/102"
    # First call uses bbox and fails, second call should not pass bbox
    assert len(calls) == 2
    assert calls[1][1] is None
    # Should use a temporary path for the second call
    assert Path(calls[1][0]) != img_path
    assert not Path(calls[1][0]).exists()

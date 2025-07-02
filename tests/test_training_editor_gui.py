import pytest

pd = pytest.importorskip("pandas")
import scanner.training_editor_gui as teg


def test_append_images(tmp_path):
    csv = tmp_path / "train.csv"
    df = teg.append_images(csv, ["a.jpg", "b.jpg"])
    assert len(df) == 2
    assert csv.exists()
    saved = pd.read_csv(csv)
    assert list(saved["image_path"]) == ["a.jpg", "b.jpg"]

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


def test_append_images_reindex(tmp_path):
    csv = tmp_path / "bad.csv"
    pd.DataFrame({"x": []}).to_csv(csv, index=False)
    df = teg.append_images(csv, ["c.jpg"])
    assert list(df.columns) == teg.DEFAULT_COLUMNS
    saved = pd.read_csv(csv)
    assert list(saved.columns) == teg.DEFAULT_COLUMNS
    assert saved.loc[0, "image_path"] == "c.jpg"

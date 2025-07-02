import pytest

pd = pytest.importorskip("pandas")
import scanner.training_dashboard as td


def test_load_data(tmp_path):
    csv = tmp_path / "cards.csv"
    csv.write_text("Name,Set,Type\nA,Base,holo\nB,Base,common\n,,\n")
    df = td.load_data(csv)
    assert len(df) == 3
    # missing values should be filled with 'Unknown'
    assert df.iloc[2]['Name'] == "Unknown"


def test_print_summary(capsys):
    df = pd.DataFrame({
        'Name': ['A', 'B'],
        'Set': ['Base', 'Base'],
        'Type': ['holo', 'common']
    })
    td.print_summary(df)
    captured = capsys.readouterr().out
    assert "Liczba kart: 2" in captured

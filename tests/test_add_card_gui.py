import pandas as pd
from viewer.add_card_gui import save_card


def test_save_card_appends_row(tmp_path):
    csv = tmp_path / "main.csv"
    csv.write_text("Name,Set,Rarity,Number,Quantity,ImagePath\n")
    row = {
        "Name": "Pikachu",
        "Set": "Base",
        "Number": "1/102",
        "Rarity": "Common",
        "Quantity": "2",
        "ImagePath": "img.jpg",
    }
    save_card(row, csv)
    df = pd.read_csv(csv)
    assert len(df) == 1
    assert df.loc[0, "Name"] == "Pikachu"
    assert df.loc[0, "Quantity"] == "2"

# dataset_builder.py

import pandas as pd
from pathlib import Path

def build_dataset(scan_dir: str | Path, csv_path: str | Path) -> None:
    """
    Uzupełnia plik CSV na podstawie zawartości folderu scan_dir,
    dodając brakujące wpisy do dataset.csv i automatycznie przypisując:
    - karton
    - rzad
    - pozycja
    - card_id
    """
    scan_dir = Path(scan_dir)
    csv_path = Path(csv_path)

    if not scan_dir.exists():
        raise FileNotFoundError(f"Nie znaleziono folderu: {scan_dir}")

    if csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=[
            "image_path", "name", "card_id", "set", "holo",
            "reverse", "karton", "rzad", "pozycja"
        ])

    existing_paths = set(df["image_path"].astype(str))
    new_rows = []
    start_index = len(df)

    new_images = [p for p in scan_dir.glob("*.jpg") if str(p.resolve()) not in existing_paths]

    for i, img_path in enumerate(new_images):
        global_pos = start_index + i + 1
        karton = (global_pos - 1) // 4000 + 1
        rzad = ((global_pos - 1) % 4000) // 1000 + 1
        pozycja = ((global_pos - 1) % 1000) + 1

        card_id = f"K{karton}_R{rzad}_P{pozycja:04d}"

        new_rows.append({
            "image_path": str(img_path.resolve()),
            "name": "", "card_id": card_id, "set": "",
            "holo": False, "reverse": False,
            "karton": karton, "rzad": rzad, "pozycja": pozycja
        })

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        df.to_csv(csv_path, index=False)

    print(f"✅ Dataset zbudowany. Liczba kart: {len(df)}")

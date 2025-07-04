import os
import shutil
import pandas as pd
from pathlib import Path

# Ścieżka do pliku CSV
csv_path = Path("scanner/dataset.csv")

# Ścieżki wyjściowe
type_output_base = Path("data/type_dataset")
card_output_base = Path("data/card_dataset")

# Wczytaj CSV
df = pd.read_csv(csv_path)

# 🧠 Funkcja określająca typ na podstawie holo/reverse
def determine_type(row):
    holo = str(row.get("holo", "")).strip().lower() == "true"
    reverse = str(row.get("reverse", "")).strip().lower() == "true"
    if holo:
        return "holo"
    if reverse:
        return "reverse"
    return "common"

# Dodaj kolumnę 'typ'
df["typ"] = df.apply(determine_type, axis=1)

# Statystyki
type_created = 0
card_created = 0
skipped = 0

for i, row in df.iterrows():
    image_path = Path(str(row["image_path"])).resolve()
    typ = str(row.get("typ", "")).strip().lower()
    card_id = str(row.get("card_id", "")).strip()

    if not image_path.exists() or not typ or not card_id or card_id.lower() == "unknown":
        skipped += 1
        continue

    # Typ folder
    type_folder = type_output_base / typ
    type_folder.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy(image_path, type_folder / image_path.name)
        type_created += 1
    except Exception:
        skipped += 1

    # Card folder
    card_folder = card_output_base / card_id
    card_folder.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy(image_path, card_folder / image_path.name)
        card_created += 1
    except Exception:
        skipped += 1

# ✅ Podsumowanie
print(f"[✓] Skopiowano {type_created} plików do 'data/type_dataset/'")
print(f"[✓] Skopiowano {card_created} plików do 'data/card_dataset/'")
if skipped:
    print(f"[!] Pominięto {skipped} wierszy z brakującymi danymi lub plikami")

import os
import shutil
import pandas as pd

# 🔧 Konfiguracja
CSV_FILE = "dataset.csv"
SOURCE_IMAGE_DIR = "scans"
OUTPUT_CARD_DIR = "dataset_card"
OUTPUT_TYPE_DIR = "dataset_type"

# 📥 Wczytaj dane
df = pd.read_csv(CSV_FILE)

# 📁 Utwórz foldery wyjściowe
os.makedirs(OUTPUT_CARD_DIR, exist_ok=True)
for type_name in ["normal", "reverse", "holo"]:
    os.makedirs(os.path.join(OUTPUT_TYPE_DIR, type_name), exist_ok=True)

# 🔁 Iteracja po rekordach
for _, row in df.iterrows():
    image = str(row["image_path"]).strip()
    card_id = str(row["card_id"]).strip()
    holo = int(row["holo"])
    reverse = int(row["reverse"])

    source = os.path.join(SOURCE_IMAGE_DIR, image)
    if not os.path.exists(source):
        print(f"⚠️ Plik nie istnieje: {source}")
        continue

    try:
        # 📁 dataset_card/<card_id>/
        card_dir = os.path.join(OUTPUT_CARD_DIR, card_id)
        os.makedirs(card_dir, exist_ok=True)
        shutil.copy2(source, os.path.join(card_dir, image))

        # 📁 dataset_type/<type>/
        if holo:
            type_dir = "holo"
        elif reverse:
            type_dir = "reverse"
        else:
            type_dir = "normal"
        shutil.copy2(source, os.path.join(OUTPUT_TYPE_DIR, type_dir, image))

    except PermissionError:
        print(f"🚫 Brak dostępu do pliku (otwarty w innym programie?): {source}")
    except Exception as e:
        print(f"❌ Błąd przy kopiowaniu {image}: {e}")

print("✅ Przygotowywanie danych zakończone.")

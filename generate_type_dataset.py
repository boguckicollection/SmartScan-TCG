import os
import shutil
from argparse import ArgumentParser
import pandas as pd
from pathlib import Path

def main() -> None:
    parser = ArgumentParser(description="Generate image dataset grouped by card type")
    parser.add_argument(
        "--csv",
        default="scanner/dataset.csv",
        help="Path to dataset CSV",
    )
    parser.add_argument(
        "--type-dir",
        default="data/type_dataset",
        help="Output directory for type-based folders",
    )
    parser.add_argument(
        "--card-dir",
        default="data/card_dataset",
        help="Output directory for card-based folders",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    type_output_base = Path(args.type_dir)
    card_output_base = Path(args.card_dir)

    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError as exc:
        raise SystemExit(
            "Dataset CSV is empty. Run 'scanner.dataset_builder.build_dataset' "
            "on your labeled card scans to populate it."
        ) from exc

    def determine_type(row):
        holo = str(row.get("holo", "")).strip().lower() == "true"
        reverse = str(row.get("reverse", "")).strip().lower() == "true"
        if holo:
            return "holo"
        if reverse:
            return "reverse"
        return "common"

    df["typ"] = df.apply(determine_type, axis=1)

    type_created = 0
    card_created = 0
    skipped = 0

    for _, row in df.iterrows():
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

    print(f"[✓] Skopiowano {type_created} plików do '{type_output_base}/'")
    print(f"[✓] Skopiowano {card_created} plików do '{card_output_base}/'")
    if skipped:
        print(f"[!] Pominięto {skipped} wierszy z brakującymi danymi lub plikami")


if __name__ == "__main__":
    main()

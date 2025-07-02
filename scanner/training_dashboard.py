import pandas as pd
import matplotlib.pyplot as plt

CSV_PATH = "cards_scanned.csv"
TARGET_COUNT = 1000


def load_data(path: str = CSV_PATH) -> pd.DataFrame:
    """Return contents of ``path`` as a DataFrame with missing values filled."""
    df = pd.read_csv(path)
    df.fillna("Unknown", inplace=True)
    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print basic dataset statistics."""
    total = len(df)
    print("\n--- Podsumowanie danych do trenowania ---")
    print(f"Liczba kart: {total}")
    print(f"Liczba unikalnych nazw: {df['Name'].nunique()}")
    print(f"Liczba unikalnych setów: {df['Set'].nunique()}")
    missing = (df == "Unknown").sum().sum()
    print(f"Brakujące dane: {missing}")
    print(
        f"Zestaw danych: {total} / {TARGET_COUNT} ({total / TARGET_COUNT * 100:.1f}%)"
    )


def plot_progress(df: pd.DataFrame) -> None:
    """Display a horizontal progress bar of dataset size versus ``TARGET_COUNT``."""
    progress = len(df)
    plt.figure(figsize=(6, 1.2))
    plt.barh(["Progres"], [progress], color="green")
    plt.xlim([0, TARGET_COUNT])
    plt.title("Postęp etykietowania")
    plt.tight_layout()
    plt.show()


def plot_distribution(df: pd.DataFrame) -> None:
    """Plot card type distribution."""
    df["Type"].value_counts().plot(kind="bar", title="Rozkład typów kart")
    plt.xlabel("Typ")
    plt.ylabel("Liczba kart")
    plt.tight_layout()
    plt.show()


def main() -> None:
    df = load_data()
    print_summary(df)
    plot_progress(df)
    plot_distribution(df)


if __name__ == "__main__":
    main()

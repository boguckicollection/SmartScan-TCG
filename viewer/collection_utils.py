"""Utilities for working with the card collection CSV."""

from pathlib import Path

import pandas as pd


def load_collection(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def merge_csv_files(paths: list[str], output: str) -> pd.DataFrame:
    """Merge multiple CSV files and save the result."""

    frames = []
    for p in paths:
        try:
            frames.append(pd.read_csv(p))
        except Exception:
            continue

    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


def missing_cards(df: pd.DataFrame, set_name: str) -> pd.DataFrame:
    """Return rows for missing cards from a given set."""
    return df[df["Set"] == set_name]

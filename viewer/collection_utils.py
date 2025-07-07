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


def append_row(csv_path: str | Path, row: dict) -> pd.DataFrame:
    """Append ``row`` as a new entry to ``csv_path`` and return the DataFrame."""
    path = Path(csv_path)
    if path.exists():
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    columns = list(df.columns)
    for key in row:
        if key not in columns:
            columns.append(key)
    df = df.reindex(columns=columns, fill_value="")
    df.loc[len(df)] = [row.get(c, "") for c in df.columns]
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df

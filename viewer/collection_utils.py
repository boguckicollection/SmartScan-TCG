"""Utilities for working with the card collection CSV."""

import pandas as pd


def load_collection(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def missing_cards(df: pd.DataFrame, set_name: str) -> pd.DataFrame:
    """Return rows for missing cards from a given set."""
    return df[df["Set"] == set_name]

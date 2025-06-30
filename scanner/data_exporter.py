"""Utilities for exporting scanned data to CSV."""

import pandas as pd


def export_to_csv(data, path: str) -> None:
    """Save list of dictionaries to CSV."""
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)

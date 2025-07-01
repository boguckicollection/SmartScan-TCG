"""Utilities for exporting scanned data to CSV."""

from pathlib import Path
import csv


def export_to_csv(data, path: str) -> None:
    """Save list of dictionaries to a CSV file.

    Parameters
    ----------
    data : list[dict]
        The rows to write. Keys of the first dictionary define the CSV
        header.
    path : str
        Destination file path.
    """

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        target.write_text("")
        return

    fieldnames = list(data[0].keys())
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

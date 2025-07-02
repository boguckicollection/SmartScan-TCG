"""Thumbnail-based collection viewer."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pandas as pd


def run(
    csv_path: str,
    master: tk.Misc | None = None,
    images_dir: str = "assets/scans",
) -> tk.Widget | None:
    """Display card thumbnails loaded from ``csv_path``.

    Parameters
    ----------
    csv_path: str
        Path to CSV file with card information.
    master: tk.Misc, optional
        Parent widget. When ``None`` a new root ``Tk`` is created.
    images_dir: str
        Directory containing card scans named ``img0001.jpg`` etc.

    Returns
    -------
    tk.Widget | None
        Created container widget when ``master`` is provided. ``None`` when a
        new root is created and ``mainloop`` is started internally.
    """
    df = pd.read_csv(csv_path)

    if master is None:
        win = tk.Tk()
        container: tk.Widget = win
        win.title("Collection Viewer")
    else:
        container = ttk.Frame(master)
        container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)
    scroll_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    images: list[ImageTk.PhotoImage] = []

    def open_detail(idx: int) -> None:
        detail = tk.Toplevel(container)
        detail.title(df.at[idx, "Name"] if "Name" in df.columns else "Card")

        img_path = Path(images_dir) / f"img{idx+1:04d}.jpg"
        if img_path.exists():
            img = Image.open(img_path)
            img.thumbnail((300, 420))
        else:
            img = Image.new("RGB", (300, 420), color="gray")
        photo = ImageTk.PhotoImage(img)
        ttk.Label(detail, image=photo).pack(padx=10, pady=10)
        detail.image = photo

        vars: dict[str, tk.StringVar] = {}
        for col in df.columns:
            frm = ttk.Frame(detail)
            frm.pack(fill="x", padx=10, pady=2)
            ttk.Label(frm, text=col, width=12).pack(side="left")
            var = tk.StringVar(value=str(df.at[idx, col]))
            ttk.Entry(frm, textvariable=var, width=30).pack(side="left", fill="x", expand=True)
            vars[col] = var

        def save() -> None:
            for col, var in vars.items():
                df.at[idx, col] = var.get()
            df.to_csv(csv_path, index=False)
            detail.destroy()

        ttk.Button(detail, text="Zapisz", command=save).pack(pady=10)

    for i, row in df.iterrows():
        img_path = Path(images_dir) / f"img{i+1:04d}.jpg"
        if img_path.exists():
            img = Image.open(img_path)
            img.thumbnail((100, 140))
        else:
            img = Image.new("RGB", (100, 140), color="gray")
        photo = ImageTk.PhotoImage(img)
        images.append(photo)
        text = row.get("Name", f"Card {i+1}")
        btn = ttk.Button(
            scroll_frame,
            image=photo,
            text=text,
            compound="top",
            command=lambda idx=i: open_detail(idx),
        )
        btn.grid(row=i // 5, column=i % 5, padx=5, pady=5)

    if master is None:
        container.mainloop()
        return None
    return container

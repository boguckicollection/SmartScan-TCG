"""List-based collection viewer with inline editing."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pandas as pd

from scanner.set_mapping import SET_MAP


def run(
    csv_path: str,
    master: tk.Misc | None = None,
    images_dir: str = "assets/scans",
) -> tk.Widget | None:
    """Display card list loaded from ``csv_path``.

    Parameters
    ----------
    csv_path : str
        Path to CSV file with card information.
    master : tk.Misc, optional
        Parent widget. When ``None`` a new root ``Tk`` is created.
    images_dir : str
        Directory containing card scans named ``img0001.jpg`` etc.

    Returns
    -------
    tk.Widget | None
        Created container widget when ``master`` is provided. ``None`` when a
        new root is created and ``mainloop`` is started internally.
    """
    df = pd.read_csv(csv_path)
    if "Set" in df.columns:
        df.sort_values("Set", inplace=True, ignore_index=True)

    if master is None:
        win = tk.Tk()
        container: tk.Widget = win
        win.title("Collection Viewer")
    else:
        container = ttk.Frame(master)
        container.pack(fill="both", expand=True)

    tree = ttk.Treeview(container, columns=list(df.columns), show="headings")
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    for i, row in df.iterrows():
        tree.insert("", "end", iid=str(i), values=list(row))
    tree.pack(fill="both", expand=True)

    images: list[ImageTk.PhotoImage] = []

    def open_detail(event: tk.Event | None = None) -> None:
        item = tree.focus()
        if not item:
            return
        idx = int(item)
        tree.pack_forget()
        detail = ttk.Frame(container)
        detail.pack(fill="both", expand=True)

        if "ImagePath" in df.columns:
            img_path = Path(df.at[idx, "ImagePath"])
        else:
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
            if col == "Set" and SET_MAP:
                values = sorted(SET_MAP.keys())
                cmb = ttk.Combobox(frm, textvariable=var, values=values)
                cmb.pack(side="left", fill="x", expand=True)
            else:
                ttk.Entry(frm, textvariable=var, width=30).pack(
                    side="left", fill="x", expand=True
                )
            vars[col] = var

        def close() -> None:
            detail.destroy()
            tree.pack(fill="both", expand=True)

        def save() -> None:
            for col, var in vars.items():
                df.at[idx, col] = var.get()
            df.to_csv(csv_path, index=False)
            tree.item(item, values=list(df.loc[idx]))
            close()

        btns = ttk.Frame(detail)
        btns.pack(pady=10)
        ttk.Button(btns, text="Zapisz", command=save).pack(side="left", padx=5)
        ttk.Button(btns, text="Anuluj", command=close).pack(side="left", padx=5)

    tree.bind("<Double-1>", open_detail)

    if master is None:
        container.mainloop()
        return None
    return container

"""Simple form for manually adding a card entry to ``data/main.csv``."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ctk

from gui_utils import init_tk_theme
from scanner import card_scanner
from . import collection_utils


DEFAULT_CSV = Path("data/main.csv")


def save_card(data: dict[str, str], csv_path: str | Path = DEFAULT_CSV) -> None:
    """Append ``data`` as a row to ``csv_path`` using ``collection_utils``."""
    collection_utils.append_row(csv_path, data)


def run(master: tk.Misc | None = None, csv_path: str | Path = DEFAULT_CSV) -> tk.Widget | None:
    """Launch the Add Card window."""
    if master is None:
        win = ctk.CTk()
        container: tk.Misc = win
        win.title("Dodaj kartę")
        init_tk_theme(win)
    else:
        win = ctk.CTkToplevel(master)
        container = win
        win.title("Dodaj kartę")

    vars: dict[str, tk.StringVar] = {}
    fields = ["Name", "Set", "Number", "Rarity", "Quantity", "ImagePath"]
    for field in fields:
        vars[field] = tk.StringVar()

    frm = ctk.CTkFrame(container, fg_color="transparent")
    frm.pack(padx=10, pady=10)

    for field in fields:
        row = ctk.CTkFrame(frm, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=field, width=10).pack(side="left")
        entry = ttk.Entry(row, textvariable=vars[field], width=40)
        entry.pack(side="left", fill="x", expand=True)
        if field == "ImagePath":
            def browse(f=field):
                path = filedialog.askopenfilename(
                    title="Wybierz obraz", filetypes=[("Image files", "*.jpg *.png")]
                )
                if path:
                    vars[f].set(path)
            ttk.Button(row, text="...", width=3, command=browse).pack(side="left")

    btns = ctk.CTkFrame(frm, fg_color="transparent")
    btns.pack(pady=5)

    def from_image() -> None:
        path = filedialog.askopenfilename(
            title="Wybierz obraz", filetypes=[("Image files", "*.jpg *.png")]
        )
        if not path:
            return
        data = card_scanner.scan_image(Path(path))
        vars["Name"].set(data.get("Name", ""))
        vars["Set"].set(data.get("Set", ""))
        vars["Number"].set(data.get("Number", ""))
        vars["Rarity"].set(data.get("Rarity", ""))
        vars["ImagePath"].set(path)
        vars["Quantity"].set("1")

    def save() -> None:
        row = {k: v.get() for k, v in vars.items()}
        save_card(row, csv_path)
        for v in vars.values():
            v.set("")

    ctk.CTkButton(btns, text="Dodaj z obrazu", command=from_image).pack(side="left", padx=5)
    ctk.CTkButton(btns, text="Zapisz", command=save).pack(side="left", padx=5)

    if master is None:
        container.mainloop()
        return None
    return container


from __future__ import annotations

"""Simple GUI for editing the training dataset."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import pandas as pd
from .set_mapping import SET_MAP
from gui_utils import init_tk_theme

from . import dataset_builder

DEFAULT_PATH = Path(__file__).resolve().parent / "dataset.csv"
DEFAULT_COLUMNS = ["image_path", "name", "card_id", "set", "holo", "reverse"]


def append_images(csv_path: str | Path, image_paths: list[str]) -> pd.DataFrame:
    """Append ``image_paths`` as new rows to ``csv_path`` and return the DataFrame."""
    path = Path(csv_path)
    if path.exists():
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=DEFAULT_COLUMNS)
    else:
        df = pd.DataFrame(columns=DEFAULT_COLUMNS)
    for p in image_paths:
        df.loc[len(df)] = [p, "", "", "", False, False]
    df.to_csv(path, index=False)
    return df


def run(csv_path: str | Path = DEFAULT_PATH, master: tk.Misc | None = None) -> tk.Widget | None:
    """Launch the editor for ``csv_path``."""
    path = Path(csv_path)
    if path.exists():
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=DEFAULT_COLUMNS)
    else:
        df = pd.DataFrame(columns=DEFAULT_COLUMNS)

    if master is None:
        win = ctk.CTk()
        container: tk.Widget = win
        win.title("Training Data Editor")
        init_tk_theme(win)
    else:
        container = ctk.CTkFrame(master, fg_color="#222222")
        container.pack(fill="both", expand=True)

    tree = ttk.Treeview(container, columns=list(df.columns), show="headings")
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=140)
    for i, row in df.iterrows():
        tree.insert("", "end", iid=str(i), values=list(row))
    tree.pack(fill="both", expand=True)

    def save_df() -> None:
        df.to_csv(path, index=False)

    def open_detail(event: tk.Event | None = None) -> None:
        item = tree.focus()
        if not item:
            return
        idx = int(item)
        tree.pack_forget()
        detail = ctk.CTkFrame(container, fg_color="#222222")
        detail.pack(fill="both", expand=True)

        img_file = Path(df.at[idx, "image_path"])
        if img_file.exists():
            img = Image.open(img_file)
            img.thumbnail((300, 420))
        else:
            img = Image.new("RGB", (300, 420), color="gray")
        photo = ImageTk.PhotoImage(img)
        ctk.CTkLabel(detail, image=photo, text="").pack(padx=10, pady=10)
        detail.image = photo

        vars: dict[str, tk.StringVar] = {}
        for col in df.columns:
            frm = ctk.CTkFrame(detail, fg_color="transparent")
            frm.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(frm, text=col, width=120).pack(side="left")
            var = tk.StringVar(value=str(df.at[idx, col]))
            if col == "set" and SET_MAP:
                values = sorted(SET_MAP.keys())
                ttk.Combobox(
                    frm,
                    textvariable=var,
                    values=values,
                    state="readonly",
                    width=30,
                ).pack(side="left")
            elif col in {"holo", "reverse"}:
                ttk.Combobox(
                    frm,
                    textvariable=var,
                    values=["True", "False"],
                    state="readonly",
                    width=30,
                ).pack(side="left")
            else:
                ttk.Entry(frm, textvariable=var, width=30).pack(side="left")
            vars[col] = var

        def close() -> None:
            detail.destroy()
            tree.pack(fill="both", expand=True)

        def save() -> None:
            for col, var in vars.items():
                df.at[idx, col] = var.get()
            save_df()
            tree.item(item, values=list(df.loc[idx]))
            close()

        btns = ctk.CTkFrame(detail, fg_color="transparent")
        btns.pack(pady=10)
        ctk.CTkButton(btns, text="Zapisz", command=save).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Anuluj", command=close).pack(side="left", padx=5)

    tree.bind("<Double-1>", open_detail)

    def add_scans() -> None:
        paths = filedialog.askopenfilenames(title="Wybierz obrazy", filetypes=[("Image files", "*.jpg *.png")])
        if not paths:
            return
        for p in paths:
            df.loc[len(df)] = [p, "", "", "", False, False]
            tree.insert("", "end", iid=str(len(df) - 1), values=list(df.loc[len(df) - 1]))
        save_df()

    def scan_images() -> None:
        paths = filedialog.askopenfilenames(
            title="Wybierz obrazy do skanowania",
            filetypes=[("Image files", "*.jpg *.png")],
        )
        if not paths:
            return
        for p in paths:
            try:
                row = dataset_builder.label_image(Path(p))
            except Exception:
                row = {c: "" for c in df.columns}
                row["image_path"] = p
            df.loc[len(df)] = [row.get(c, "") for c in df.columns]
            tree.insert("", "end", iid=str(len(df) - 1), values=list(df.loc[len(df) - 1]))
        save_df()

    btn_frame = ctk.CTkFrame(container, fg_color="transparent")
    btn_frame.pack(pady=5)
    ctk.CTkButton(btn_frame, text="Dodaj skany", command=add_scans).pack(side="left")
    ctk.CTkButton(btn_frame, text="Skanuj karty", command=scan_images).pack(side="left", padx=5)

    if master is None:
        container.mainloop()
        return None
    return container


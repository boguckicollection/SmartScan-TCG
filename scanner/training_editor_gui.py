from __future__ import annotations

"""Simple GUI for editing the training dataset."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import pandas as pd
from .set_mapping import SET_MAP


class FilterableCombobox(ttk.Combobox):
    """Combobox that filters its values as the user types."""

    def __init__(self, master: tk.Widget | None, values: list[str], **kwargs) -> None:
        super().__init__(master, values=values, **kwargs)
        self._all_values = list(values)
        self.bind("<KeyRelease>", self._on_keyrelease)

    def _on_keyrelease(self, event: tk.Event) -> None:
        pattern = self.get().lower()
        filtered = [v for v in self._all_values if pattern in v.lower()]
        self["values"] = filtered if filtered else self._all_values

# Reverse lookup of set names to their abbreviations
INV_SET_MAP: dict[str, str] = {v: k for k, v in SET_MAP.items()}
from gui_utils import init_tk_theme



DEFAULT_PATH = Path(__file__).resolve().parent / "dataset.csv"
DEFAULT_COLUMNS = [
    "image_path",
    "name",
    "card_id",
    "set",
    "holo",
    "reverse",
    "karton",
    "rzad",
    "pozycja",
]


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

    if list(df.columns) != DEFAULT_COLUMNS:
        df = df.reindex(columns=DEFAULT_COLUMNS, fill_value="")

    for p in image_paths:
        df.loc[len(df)] = [p, "", "", "", False, False, "", "", ""]
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
            value = str(df.at[idx, col])
            if col == "set" and SET_MAP:
                display = SET_MAP.get(value.upper(), value)
                var = tk.StringVar(value=display)
                values = sorted(SET_MAP.values())
                FilterableCombobox(
                    frm,
                    textvariable=var,
                    values=values,
                    state="normal",
                    width=30,
                ).pack(side="left")
            elif col in {"holo", "reverse"}:
                var = tk.StringVar(value=value)
                ttk.Combobox(
                    frm,
                    textvariable=var,
                    values=["True", "False"],
                    state="readonly",
                    width=30,
                ).pack(side="left")
            else:
                var = tk.StringVar(value=value)
                ttk.Entry(frm, textvariable=var, width=30).pack(side="left")
            vars[col] = var

        def close() -> None:
            detail.destroy()
            tree.pack(fill="both", expand=True)

        def save() -> None:
            for col, var in vars.items():
                val = var.get()
                if col == "set" and SET_MAP:
                    val = INV_SET_MAP.get(val, val)
                df.at[idx, col] = val
            # generate new card_id from karton/rzad/pozycja
            karton = df.at[idx, "karton"]
            rzad = df.at[idx, "rzad"]
            pos = df.at[idx, "pozycja"]
            try:
                pos_int = max(0, min(int(pos), 1000))
            except ValueError:
                pos_int = 0
            df.at[idx, "pozycja"] = str(pos_int)
            if karton and rzad and pos:
                df.at[idx, "card_id"] = f"K{karton}_R{rzad}_P{pos_int:04d}"
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
        if list(df.columns) != DEFAULT_COLUMNS:
            messagebox.showerror(
                "Błędne kolumny",
                "CSV ma niezgodne kolumny i nie można dodać wierszy.",
            )
            return
        for p in paths:
            df.loc[len(df)] = [p, "", "", "", False, False, "", "", ""]
            tree.insert("", "end", iid=str(len(df) - 1), values=list(df.loc[len(df) - 1]))
        save_df()

    btn_frame = ctk.CTkFrame(container, fg_color="transparent")
    btn_frame.pack(pady=5)
    ctk.CTkButton(btn_frame, text="Dodaj skany", command=add_scans).pack(side="left")

    if master is None:
        container.mainloop()
        return None
    return container


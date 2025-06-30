"""Simple CSV viewer with search and filtering."""

import tkinter as tk
from tkinter import ttk
import pandas as pd


def run(path: str):
    df = pd.read_csv(path)
    root = tk.Tk()
    root.title("Collection Viewer")

    tree = ttk.Treeview(root, columns=list(df.columns), show="headings")
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))
    tree.pack(fill="both", expand=True)

    root.mainloop()

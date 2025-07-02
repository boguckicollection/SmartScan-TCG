"""Common helpers for initializing Tkinter GUIs."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import sv_ttk


TITLE_FONT = ("Segoe UI", 18, "bold")
FOOTER_FONT = ("Segoe UI", 8)

def init_tk_theme(win: tk.Tk) -> None:
    """Apply common window settings and sv-ttk theme."""
    win.geometry("900x600")
    win.resizable(True, True)
    sv_ttk.set_theme("dark")
    style = ttk.Style(win)
    style.configure("TLabel", font=("Segoe UI", 10))



def set_window_icon(win: tk.Tk, icon_path: str | None = None) -> None:
    """Set window icon if the file exists."""
    if icon_path:
        try:
            win.iconphoto(False, tk.PhotoImage(file=icon_path))
        except Exception:
            pass


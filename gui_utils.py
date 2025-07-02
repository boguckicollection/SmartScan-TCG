"""Common helpers for initializing Tkinter GUIs."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import sv_ttk


TITLE_FONT = ("Segoe UI", 18, "bold")
FOOTER_FONT = ("Segoe UI", 8)

def init_tk_theme(win: tk.Misc) -> None:
    """Apply common window settings and default themes."""
    win.geometry("900x600")
    win.resizable(True, True)
    if isinstance(win, ctk.CTk):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        style = ttk.Style()
    else:
        sv_ttk.set_theme("dark")
        style = ttk.Style(win)
    style.configure("TLabel", font=("Segoe UI", 10))



def set_window_icon(win: tk.Misc, icon_path: str | None = None) -> None:
    """Set window icon if the file exists."""
    if icon_path:
        try:
            win.iconphoto(False, tk.PhotoImage(file=icon_path))
        except Exception:
            pass


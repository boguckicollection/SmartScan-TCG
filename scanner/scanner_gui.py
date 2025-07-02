"""GUI for scanning and labeling Pokemon TCG cards."""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from gui_utils import init_tk_theme


def run():
    root = ctk.CTk()
    root.title("Card Scanner")
    init_tk_theme(root)
    ttk.Label(root, text="Scanner placeholder").pack(padx=20, pady=20)
    root.mainloop()

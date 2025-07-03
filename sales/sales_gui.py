"""GUI for reviewing sales data and generating reports."""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from gui_utils import init_tk_theme


def run():
    root = ctk.CTk()
    root.title("Sales Analyzer")
    init_tk_theme(root)
    ttk.Label(root, text="Sales analyzer placeholder").pack(padx=20, pady=20)
    root.mainloop()

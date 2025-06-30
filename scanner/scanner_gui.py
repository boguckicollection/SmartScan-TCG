"""GUI for scanning and labeling Pokemon TCG cards."""

import tkinter as tk
from tkinter import ttk


def run():
    root = tk.Tk()
    root.title("Card Scanner")
    ttk.Label(root, text="Scanner placeholder").pack(padx=20, pady=20)
    root.mainloop()

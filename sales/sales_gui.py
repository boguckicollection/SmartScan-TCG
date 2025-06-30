"""GUI for reviewing sales data and generating reports."""

import tkinter as tk
from tkinter import ttk


def run():
    root = tk.Tk()
    root.title("Sales Analyzer")
    ttk.Label(root, text="Sales analyzer placeholder").pack(padx=20, pady=20)
    root.mainloop()

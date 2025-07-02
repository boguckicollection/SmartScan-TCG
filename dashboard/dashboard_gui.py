"""Simple dashboard GUI for viewing collection statistics."""

from __future__ import annotations

from pathlib import Path
import random
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from gui_utils import init_tk_theme, TITLE_FONT

DATA_FILE = Path("data/main.csv")


class DashboardFrame(ttk.Frame):
    """Dashboard view that can be embedded in another window."""

    def __init__(self, master: tk.Misc, show_sidebar: bool = True) -> None:
        super().__init__(master)

        self._sidebar: ttk.Frame | None = None
        if show_sidebar:
            self._sidebar = ttk.Frame(self)
            self._sidebar.pack(side="left", fill="y", padx=0, pady=0)
            ttk.Label(
                self._sidebar,
                text="SmartScan TCG",
                font=TITLE_FONT,
                padding=10,
            ).pack()
            for name in [
                "Dashboard",
                "Kolekcja",
                "Skanowanie",
                "Sprzedaż",
                "Statystyki",
                "Ustawienia",
            ]:
                ttk.Button(self._sidebar, text=name, width=20).pack(pady=2, padx=5)

        self._content = ttk.Frame(self)
        self._content.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self._stats_frame = ttk.Frame(self._content)
        self._stats_frame.pack(fill="x")
        self._charts_frame = ttk.Frame(self._content)
        self._charts_frame.pack(fill="both", expand=True)
        self._table_frame = ttk.Frame(self._content)
        self._table_frame.pack(fill="both", expand=True, pady=10)

        self.load_data()
        self.create_stat_boxes()
        self.create_charts()
        self.create_sets_table()

    def load_data(self) -> None:
        if DATA_FILE.exists():
            self.df = pd.read_csv(DATA_FILE)
        else:
            self.df = pd.DataFrame(columns=["Name", "Set", "Rarity", "Number"])

    # --- Stats -------------------------------------------------------------
    def create_stat_boxes(self) -> None:
        total_cards = len(self.df)
        unique_cards = self.df["Name"].nunique() if not self.df.empty else 0
        total_sets = self.df["Set"].nunique() if not self.df.empty else 0
        growth_week = 0
        if "Date" in self.df.columns:
            last_week = pd.Timestamp.today() - pd.Timedelta(days=7)
            growth_week = int((self.df["Date"] >= last_week).sum())
        for i, (label, value) in enumerate(
            [
                ("Liczba kart", total_cards),
                ("Wzrost (7d)", growth_week),
                ("Unikalne karty", unique_cards),
                ("Sety", total_sets),
            ]
        ):
            frame = ttk.Frame(self._stats_frame, padding=10, relief="ridge")
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            ttk.Label(frame, text=str(value), font=TITLE_FONT).pack()
            ttk.Label(frame, text=label).pack()
        for i in range(4):
            self._stats_frame.columnconfigure(i, weight=1)

    # --- Charts ------------------------------------------------------------
    def _to_mpl_color(self, color: str) -> str:
        """Convert Tk color names to a hex string for Matplotlib."""
        try:
            r, g, b = self.winfo_rgb(color)
        except tk.TclError:
            return color
        return f"#{r//256:02x}{g//256:02x}{b//256:02x}"

    def create_charts(self) -> None:
        try:
            bg = self.cget("background")
        except tk.TclError:
            bg = self.winfo_toplevel().cget("background")
        mpl_bg = self._to_mpl_color(bg)
        line_fig = Figure(figsize=(4, 3), dpi=100, facecolor=mpl_bg)
        ax = line_fig.add_subplot(111, facecolor=mpl_bg)
        if "Date" in self.df.columns:
            counts = self.df.groupby("Date").size().sort_index()
            ax.plot(counts.index, counts.values, marker="o")
        else:
            days = list(range(1, 31))
            vals = [random.randint(0, len(self.df) or 1) for _ in days]
            ax.plot(days, vals, marker="o")
        ax.set_title("Liczba kart vs czas")
        ax.set_xlabel("Dzień")
        ax.set_ylabel("Ilość")
        line_fig.tight_layout()
        canvas = FigureCanvasTkAgg(line_fig, master=self._charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        pie_fig = Figure(figsize=(4, 3), dpi=100, facecolor=mpl_bg)
        ax2 = pie_fig.add_subplot(111, facecolor=mpl_bg)
        if "Rarity" in self.df.columns and not self.df.empty:
            counts = self.df["Rarity"].value_counts()
            ax2.pie(counts.values, labels=counts.index, autopct="%1.0f%%")
        else:
            ax2.pie([1], labels=["Brak danych"])
        ax2.set_title("Typy kart")
        pie_fig.tight_layout()
        canvas2 = FigureCanvasTkAgg(pie_fig, master=self._charts_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(side="left", fill="both", expand=True)

    # --- Table -------------------------------------------------------------
    def create_sets_table(self) -> None:
        columns = ("Set", "Ilość")
        tree = ttk.Treeview(self._table_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
        if not self.df.empty:
            for set_name, group in self.df.groupby("Set"):
                tree.insert("", "end", values=(set_name, len(group)))
        tree.pack(fill="both", expand=True)


class Dashboard(ctk.CTk):
    """Main dashboard window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("SmartScan Dashboard")
        init_tk_theme(self)
        self.configure(bg="#222222")

        DashboardFrame(self, show_sidebar=True).pack(fill="both", expand=True)


def run() -> None:
    Dashboard().mainloop()


if __name__ == "__main__":
    run()

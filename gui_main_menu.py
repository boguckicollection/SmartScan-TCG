import os
import tkinter as tk
from tkinter import ttk


def start_scan():
    print("> Tryb: Skanowanie kart")
    # import scanner.scanner_gui
    # scanner.scanner_gui.run()

def start_viewer():
    print("> Tryb: Przeglądanie kolekcji")
    # import viewer.viewer_gui
    # viewer.viewer_gui.run()

def start_sales():
    print("> Tryb: Analiza sprzedaży (Shoper)")
    # import sales.sales_gui
    # sales.sales_gui.run()


def main():
    root = tk.Tk()
    root.title("TCG Organizer")
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(icon_path):
        root.iconphoto(False, tk.PhotoImage(file=icon_path))
    root.geometry("400x420")
    root.resizable(False, False)

    # Styl minimalistyczny (Windows 11 look)
    style = ttk.Style(root)
    root.tk.call("source", "assets/config/azure.tcl")
    style.theme_use("azure-light")  # albo "azure-dark"

    ttk.Label(root, text="TCG Organizer", font=("Segoe UI", 18, "bold")).pack(pady=(30, 10))
    ttk.Label(root, text="Wybierz tryb pracy", font=("Segoe UI", 11)).pack(pady=(0, 20))

    # Przycisk: skanowanie
    ttk.Button(root, text="1. Skanowanie kart", command=start_scan, width=30).pack(pady=10)

    # Przycisk: przeglądanie kolekcji
    ttk.Button(root, text="2. Przeglądanie kolekcji", command=start_viewer, width=30).pack(pady=10)

    # Przycisk: analiza sprzedaży
    ttk.Button(root, text="3. Analiza sprzedaży (Shoper)", command=start_sales, width=30).pack(pady=10)

    # Stopka
    ttk.Label(root, text="v1.0 | by TCG Project", font=("Segoe UI", 8)).pack(side="bottom", pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()

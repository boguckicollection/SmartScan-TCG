import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from scanner import card_scanner


def start_scan():
    paths = filedialog.askopenfilenames(
        title="Wybierz skany kart",
        filetypes=[("Image files", "*.jpg *.png")],
    )
    if not paths:
        return

    progress_win = tk.Toplevel()
    progress_win.title("Postęp skanowania")
    ttk.Label(progress_win, text="Skanowanie kart...").pack(padx=20, pady=(20, 10))
    progress_var = tk.DoubleVar(value=0)
    progress = ttk.Progressbar(progress_win, variable=progress_var, maximum=len(paths), length=300)
    progress.pack(padx=20, pady=10)
    status = ttk.Label(progress_win, text=f"0 / {len(paths)}")
    status.pack(pady=(0, 20))

    def update_progress(current: int, total: int) -> None:
        progress_var.set(current)
        status.config(text=f"{current} / {total}")
        progress_win.update_idletasks()

    data = card_scanner.scan_files([Path(p) for p in paths], progress_callback=update_progress)
    progress_win.destroy()
    output = Path("data/cards_scanned.csv")
    card_scanner.export_to_csv(data, str(output))
    messagebox.showinfo(
        "Skanowanie zakonczone",
        f"Zapisano {len(data)} rekordy do {output}"
    )

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

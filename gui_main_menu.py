from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
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

    ttk.Label(progress_win, text="Skanowanie kart...").pack(padx=20, pady=(20, 5))

    scans_dir = Path(__file__).resolve().parent / "assets" / "scans"
    card_paths = sorted(scans_dir.glob("*.jpg"))[:10]
    images = []
    for p in card_paths:
        try:
            img = Image.open(p)
            img.thumbnail((150, 210))
            images.append(ImageTk.PhotoImage(img))
        except Exception:
            continue

    img_label = ttk.Label(progress_win)
    img_label.pack(pady=(5, 10))
    progress_win.card_images = images

    idx = 0
    running = True

    def animate() -> None:
        nonlocal idx
        if not running or not images:
            return
        img_label.configure(image=images[idx])
        idx = (idx + 1) % len(images)
        progress_win.after(200, animate)

    animate()

    progress_var = tk.DoubleVar(value=0)
    progress = ttk.Progressbar(
        progress_win, variable=progress_var, maximum=len(paths), length=300
    )
    progress.pack(padx=20, pady=10)
    status = ttk.Label(progress_win, text=f"0 / {len(paths)}")
    status.pack(pady=(0, 20))

    def update_progress(current: int, total: int) -> None:
        progress_var.set(current)
        status.config(text=f"{current} / {total}")
        progress_win.update()

    data = card_scanner.scan_files([Path(p) for p in paths], progress_callback=update_progress)
    running = False
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
    icon_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    if icon_path.exists():
        root.iconphoto(False, tk.PhotoImage(file=icon_path))
    root.geometry("400x480")
    root.resizable(False, False)

    # Styl minimalistyczny (Windows 11 look)
    style = ttk.Style(root)
    root.tk.call("source", "assets/config/azure.tcl")
    style.theme_use("azure-light")  # albo "azure-dark"

    logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    if logo_path.exists():
        # shrink the logo and place it next to the title
        img = Image.open(logo_path)
        img.thumbnail((48, 48))
        logo_img = ImageTk.PhotoImage(img)
        header = ttk.Frame(root)
        header.pack(pady=(20, 10))
        ttk.Label(header, image=logo_img).pack(side="left", padx=(0, 10))
        ttk.Label(header, text="TCG Organizer", font=("Segoe UI", 18, "bold")).pack(side="left")
        root.logo_img = logo_img
    else:
        ttk.Label(root, text="TCG Organizer", font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
    ttk.Label(root, text="Wybierz tryb pracy", font=("Segoe UI", 11)).pack(pady=(0, 20))

    # Przycisk: skanowanie
    ttk.Button(root, text="1. Skanowanie kart", command=start_scan, style="Accent.TButton", width=28).pack(pady=10)

    # Przycisk: przeglądanie kolekcji
    ttk.Button(root, text="2. Przeglądanie kolekcji", command=start_viewer, style="Accent.TButton", width=28).pack(pady=10)

    # Przycisk: analiza sprzedaży
    ttk.Button(root, text="3. Analiza sprzedaży (Shoper)", command=start_sales, style="Accent.TButton", width=28).pack(pady=10)

    # Stopka
    ttk.Label(root, text="power by boguckicollection", font=("Segoe UI", 8)).pack(side="bottom", pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()

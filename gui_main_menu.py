from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from scanner import card_scanner
import sv_ttk

_root: tk.Tk | None = None
_sidebar: ttk.Frame | None = None
_content: ttk.Frame | None = None


def clear_content() -> None:
    """Remove all widgets from the content frame."""
    if _content is not None:
        for widget in _content.winfo_children():
            widget.destroy()


def build_sidebar() -> None:
    """Create navigation buttons on the sidebar."""
    if _sidebar is None:
        return
    for widget in _sidebar.winfo_children():
        widget.destroy()
    ttk.Button(
        _sidebar,
        text="Dashboard",
        command=start_dashboard,
        width=18,
    ).pack(pady=2, fill="x")
    ttk.Button(
        _sidebar,
        text="Skanowanie kart",
        command=start_scan,
        width=18,
    ).pack(pady=2, fill="x")
    ttk.Button(
        _sidebar,
        text="Przeglądanie kolekcji",
        command=start_viewer,
        width=18,
    ).pack(pady=2, fill="x")
    ttk.Button(
        _sidebar,
        text="Analiza sprzedaży",
        command=start_sales,
        width=18,
    ).pack(pady=2, fill="x")


def start_dashboard() -> None:
    """Display the dashboard in the content area."""
    clear_content()
    if _content is None:
        return
    from dashboard.dashboard_gui import DashboardFrame
    DashboardFrame(_content, show_sidebar=False).pack(fill="both", expand=True)


def start_scan() -> None:
    paths = filedialog.askopenfilenames(
        title="Wybierz skany kart",
        filetypes=[("Image files", "*.jpg *.png")],
    )
    if not paths:
        return
    show_scan_progress([Path(p) for p in paths])


def show_scan_progress(paths: list[Path]) -> None:
    clear_content()
    if _content is None:
        return

    frame = ttk.Frame(_content)
    frame.pack(pady=20)

    ttk.Label(frame, text="Skanowanie kart...").pack(padx=20, pady=(0, 5))

    scans_dir = Path(__file__).resolve().parent / "assets" / "scans"
    card_paths = sorted(scans_dir.glob("*.jpg"))[:10]
    images: list[ImageTk.PhotoImage] = []
    for p in card_paths:
        try:
            img = Image.open(p)
            img.thumbnail((150, 210))
            images.append(ImageTk.PhotoImage(img))
        except Exception:
            continue

    img_label = ttk.Label(frame)
    img_label.pack(pady=(5, 10))
    frame.card_images = images

    idx = 0
    running = True

    def animate() -> None:
        nonlocal idx
        if not running or not images:
            return
        img_label.configure(image=images[idx])
        idx = (idx + 1) % len(images)
        frame.after(200, animate)

    animate()

    progress_var = tk.DoubleVar(value=0)
    progress = ttk.Progressbar(frame, variable=progress_var, maximum=len(paths), length=300)
    progress.pack(padx=20, pady=10)
    status = ttk.Label(frame, text=f"0 / {len(paths)}")
    status.pack(pady=(0, 10))

    back_btn = ttk.Button(frame, text="Powrót", command=start_dashboard, state="disabled")
    back_btn.pack(pady=(10, 0))

    def update_progress(current: int, total: int) -> None:
        progress_var.set(current)
        status.config(text=f"{current} / {total}")
        frame.update()

    data = card_scanner.scan_files(paths, progress_callback=update_progress)
    running = False
    output = Path("data/cards_scanned.csv")
    card_scanner.export_to_csv(data, str(output))
    messagebox.showinfo(
        "Skanowanie zakonczone",
        f"Zapisano {len(data)} rekordy do {output}"
    )
    back_btn.config(state="normal")


def start_viewer() -> None:
    """Open the collection viewer for ``data/cards_batch_0001.csv``."""
    csv_path = Path("data/cards_batch_0001.csv")
    if not csv_path.exists():
        messagebox.showerror("Brak pliku", f"Nie znaleziono {csv_path}")
        return
    import viewer.viewer_gui as viewer_gui
    clear_content()
    if _content is None:
        return
    frame = ttk.Frame(_content)
    frame.pack(fill="both", expand=True)
    viewer_gui.run(str(csv_path), master=frame)
    ttk.Button(frame, text="Powrót", command=start_dashboard).pack(pady=10)

def start_sales():
    print("> Tryb: Analiza sprzedaży (Shoper)")
    # import sales.sales_gui
    # sales.sales_gui.run()


def main():
    global _root, _sidebar, _content
    root = tk.Tk()
    _root = root
    root.title("TCG Organizer")
    icon_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    if icon_path.exists():
        root.iconphoto(False, tk.PhotoImage(file=icon_path))
    root.geometry("900x600")
    root.resizable(True, True)

    # Styl "Sun Valley" (sv-ttk) przypominający Windows 11
    style = ttk.Style(root)
    sv_ttk.set_theme("dark")

    logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    if logo_path.exists():
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

    body = ttk.Frame(root)
    body.pack(fill="both", expand=True)

    _sidebar = ttk.Frame(body)
    _sidebar.pack(side="left", fill="y", padx=10, pady=10)

    _content = ttk.Frame(body)
    _content.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    ttk.Label(root, text="power by boguckicollection", font=("Segoe UI", 8)).pack(side="bottom", pady=10)

    build_sidebar()
    start_dashboard()
    root.mainloop()


if __name__ == "__main__":
    main()

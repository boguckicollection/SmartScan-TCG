from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
from scanner import card_scanner
from gui_utils import (
    init_tk_theme,
    set_window_icon,
    TITLE_FONT,
    FOOTER_FONT,
)


_root: ctk.CTk | None = None
_sidebar: ctk.CTkFrame | None = None
_content: ctk.CTkFrame | None = None
_nav_buttons: dict[str, ctk.CTkButton] = {}


def _on_nav(btn: ctk.CTkButton, cmd) -> None:
    """Highlight the active navigation button and execute its command."""
    for b in _nav_buttons.values():
        b.configure(fg_color="#333333")
    btn.configure(fg_color="#555555")
    cmd()


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
    def add_btn(name: str, cmd) -> None:
        btn = ctk.CTkButton(
            _sidebar,
            text=name,
            command=lambda: _on_nav(btn, cmd),
            width=140,
        )
        btn.pack(pady=6, fill="x", padx=5)
        _nav_buttons[name] = btn

    add_btn("📊 Dashboard", start_dashboard)
    add_btn("📚 Przeglądanie kolekcji", start_viewer)
    add_btn("➕ Dodaj kartę", start_add_card)
    add_btn("🔗 Scal CSV", merge_csv_dialog)
    add_btn("💰 Analiza sprzedaży", start_sales)


def start_dashboard() -> None:
    """Display the dashboard in the content area."""
    if "📊 Dashboard" in _nav_buttons:
        _on_nav(_nav_buttons["📊 Dashboard"], lambda: None)
    clear_content()
    if _content is None:
        return
    from dashboard.dashboard_gui import DashboardFrame
    DashboardFrame(_content, show_sidebar=False).pack(fill="both", expand=True)


def start_scan() -> None:
    if "📷 Skanowanie kart" in _nav_buttons:
        _on_nav(_nav_buttons["📷 Skanowanie kart"], lambda: None)
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

    frame = ctk.CTkFrame(_content, fg_color="transparent")
    frame.pack(pady=20)

    ctk.CTkLabel(frame, text="Skanowanie kart... 🃏").pack(padx=20, pady=(0, 5))

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
    status = ctk.CTkLabel(frame, text=f"0 / {len(paths)}")
    status.pack(pady=(0, 10))

    back_btn = ctk.CTkButton(frame, text="Powrót", command=start_dashboard, state="disabled")
    back_btn.pack(pady=(10, 0))

    def update_progress(current: int, total: int) -> None:
        progress_var.set(current)
        status.config(text=f"{current} / {total}")
        frame.update()

    data = card_scanner.scan_files(paths, progress_callback=update_progress)
    running = False
    show_scan_results(data)
    back_btn.config(state="normal")


def show_scan_results(data: list[dict]) -> None:
    """Display scanned card information and allow saving to CSV."""
    if _content is None:
        return

    clear_content()
    frame = ctk.CTkFrame(_content, fg_color="transparent")
    frame.pack(fill="both", expand=True)

    columns = ["CardID", "Name", "Number", "Set", "Type"]
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    for row in data:
        values = [row.get(c, "") for c in columns]
        tree.insert("", "end", values=values)
    tree.pack(side="left", fill="both", expand=True, pady=10)
    vsb.pack(side="right", fill="y")

    def save() -> None:
        save_path = filedialog.asksaveasfilename(
            title="Zapisz dane skanowania",
            initialdir="data",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )
        if save_path:
            card_scanner.export_to_csv(data, save_path)
            messagebox.showinfo(
                "Skanowanie zakonczone",
                f"Zapisano {len(data)} rekordów do {save_path}"
            )

    btns = ctk.CTkFrame(frame, fg_color="transparent")
    btns.pack(pady=10)
    ctk.CTkButton(btns, text="Zapisz do CSV", command=save).pack(side="left", padx=5)
    ctk.CTkButton(btns, text="Powrót", command=start_dashboard).pack(side="left", padx=5)


def start_viewer() -> None:
    """Open the collection viewer for ``data/main.csv``."""
    if "📚 Przeglądanie kolekcji" in _nav_buttons:
        _on_nav(_nav_buttons["📚 Przeglądanie kolekcji"], lambda: None)
    csv_path = Path("data/main.csv")
    if not csv_path.exists():
        messagebox.showerror("Brak pliku", f"Nie znaleziono {csv_path}")
        return
    import viewer.viewer_gui as viewer_gui
    clear_content()
    if _content is None:
        return
    frame = ctk.CTkFrame(_content, fg_color="transparent")
    frame.pack(fill="both", expand=True)
    viewer_gui.run(str(csv_path), master=frame, page_size=50)
    ctk.CTkButton(frame, text="Powrót", command=start_dashboard).pack(pady=10)


def start_add_card() -> None:
    """Open the add card dialog window."""
    import viewer.add_card_gui as add_gui
    add_gui.run(_root, csv_path=Path("data/main.csv"))


def start_training_editor() -> None:
    """Open editor for the training dataset."""
    if "📝 Edycja treningu" in _nav_buttons:
        _on_nav(_nav_buttons["📝 Edycja treningu"], lambda: None)
    csv_path = Path("scanner/dataset.csv")
    clear_content()
    if _content is None:
        return
    import scanner.training_editor_gui as teg
    frame = ctk.CTkFrame(_content, fg_color="transparent")
    frame.pack(fill="both", expand=True)
    teg.run(str(csv_path), master=frame)
    ctk.CTkButton(frame, text="Powrót", command=start_dashboard).pack(pady=10)


def merge_csv_dialog() -> None:
    """Merge selected CSV files into ``data/main.csv``."""
    if "🔗 Scal CSV" in _nav_buttons:
        _on_nav(_nav_buttons["🔗 Scal CSV"], lambda: None)
    paths = filedialog.askopenfilenames(
        title="Wybierz pliki CSV",
        initialdir="data",
        filetypes=[("CSV", "*.csv")],
    )
    if not paths:
        return
    from viewer.collection_utils import merge_csv_files
    output = Path("data/main.csv")
    merge_csv_files(list(paths), str(output))
    messagebox.showinfo(
        "Scalanie zakonczone",
        f"Zapisano dane do {output}"
    )

def start_sales():
    if "💰 Analiza sprzedaży" in _nav_buttons:
        _on_nav(_nav_buttons["💰 Analiza sprzedaży"], lambda: None)
    print("> Tryb: Analiza sprzedaży (Shoper)")
    # import sales.sales_gui
    # sales.sales_gui.run()


def main():
    global _root, _sidebar, _content
    root = ctk.CTk()
    _root = root
    root.title("SmartScanTCG")
    icon_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    set_window_icon(root, str(icon_path) if icon_path.exists() else None)
    init_tk_theme(root)

    bg_path = Path(__file__).resolve().parent / "assets" / "backgroung.png"
    if bg_path.exists():
        bg_img = Image.open(bg_path)
        bg_img = bg_img.resize((900, 600))
        bg_photo = ctk.CTkImage(bg_img)
        bg_label = ctk.CTkLabel(root, image=bg_photo, text="")
        bg_label.place(relx=0.5, rely=0.5, relwidth=1, relheight=1, anchor="center")
        bg_label.lower()
        root.bg_photo = bg_photo

    body = ctk.CTkFrame(root, fg_color="transparent")
    body.pack(fill="both", expand=True)

    sidebar_bar = ctk.CTkFrame(body, fg_color="transparent", width=6)
    sidebar_bar.pack(side="left", fill="y")

    _sidebar = ctk.CTkFrame(body, fg_color="transparent", width=150)
    _sidebar.pack(side="left", fill="y", padx=(0, 20), pady=10)

    logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    if logo_path.exists():
        img = Image.open(logo_path)
        img.thumbnail((48, 48))
        logo_img = ctk.CTkImage(img)
        header = ctk.CTkFrame(_sidebar, fg_color="transparent")
        header.pack(pady=(10, 20))
        ctk.CTkLabel(header, image=logo_img, text="").pack(side="left", padx=(0, 10))
        ctk.CTkLabel(header, text="SmartScanTCG", font=TITLE_FONT).pack(side="left")
        root.logo_img = logo_img
    else:
        ctk.CTkLabel(_sidebar, text="SmartScanTCG", font=TITLE_FONT).pack(pady=(10, 20))

    _content = ctk.CTkFrame(body, fg_color="transparent")
    _content.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    ctk.CTkLabel(root, text="power by boguckicollection", font=FOOTER_FONT).pack(side="bottom", pady=10)

    build_sidebar()
    if "📊 Dashboard" in _nav_buttons:
        _on_nav(_nav_buttons["📊 Dashboard"], start_dashboard)
    else:
        start_dashboard()
    root.mainloop()


if __name__ == "__main__":
    main()

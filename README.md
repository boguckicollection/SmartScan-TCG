# TCG Organizer

<p align="center">
  <img src="assets/logo.png" alt="TCG Organizer Logo" width="200" />
</p>

TCG Organizer provides a simple GUI for scanning cards, browsing your collection, and analyzing sales data. The application uses a Tkinter-based interface and relies on optional Azure theme assets located in the `assets/config` directory.

## Running the application

Install dependencies from `requirements.txt` and launch the main menu:

```bash
pip install -r requirements.txt
python main.py
```

The main menu lets you choose between scanning cards, viewing your collection, or analyzing Shoper sales.

## Scanning cards from images

Scans of cards placed in `assets/scans` can be processed in batch using
`scanner/card_scanner.py`. Execute the script from the repository root so that
the ``scanner`` package is discoverable. The script performs OCR on each image
and stores the results in `data/cards_scanned.csv`:

```bash
python scanner/card_scanner.py
```

Alternatively you can launch it as a module:

```bash
python -m scanner.card_scanner
```

You can also execute the script from within the ``scanner`` directory:

```bash
cd scanner
python card_scanner.py
```

Ensure the `tesseract` binary is installed and available in your `PATH` for OCR
to work correctly. If you are on Windows, download the installer from
[UB Mannheim's release page](https://github.com/UB-Mannheim/tesseract/wiki) and
add the installation directory (e.g. `C:\\Program Files\\Tesseract-OCR`) to
your `PATH`. Alternatively set the `TESSERACT_CMD` environment variable to the
full path of `tesseract.exe`.

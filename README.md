# TCG Organizer

<p align="center">
  <img src="assets/logo.png" alt="TCG Organizer Logo" width="200" />
</p>

TCG Organizer provides a simple GUI for scanning cards, browsing your collection, and analyzing sales data. The application uses a Tkinter-based interface styled with the optional `sv-ttk` Sun Valley theme.

## Running the application

Install dependencies from `requirements.txt` and launch the main menu:

```bash
pip install -r requirements.txt
python main.py
```

The main menu lets you choose between scanning cards, viewing your collection, analyzing Shoper sales, or opening a dashboard with basic statistics.
Selecting **Skanowanie kart** opens a dialog where you can choose image files from disk. After scanning you
can save the results to a CSV file inside the chosen directory (e.g. `data/K1/R3/50.csv`).
Multiple such files can later be merged into `data/main.csv` from the main menu.

The main window now displays the project logo at the top. During scanning an
animation of sample cards plays above the progress bar providing visual
feedback.

## Scanning cards from images

Scans of cards placed in `assets/scans` can be processed in batch using
`scanner/card_scanner.py`. Execute the script from the repository root so that
the ``scanner`` package is discoverable. The script performs OCR on each image
and lets you save the results to a CSV file of your choice. It automatically crops
regions with the card name and set information before running OCR to improve
accuracy:

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

## Pretrained models

Scanning cards also requires two PyTorch models located inside the
`scanner/` directory:

- `card_model.pt` &ndash; predicts the card identifier
- `type_model.pt` &ndash; detects whether the scan is a holo, reverse or
 common card

Download the pretrained weights from the project's releases page and place the
files directly in the `scanner/` folder. If downloads are unavailable you can
train the models yourself:

1. Run `scanner.dataset_builder.build_dataset` on a directory of labeled card
   scans to create `dataset.csv`. The generated CSV contains the columns
   `image_path`, `name`, `card_id`, `set`, `holo`, `reverse`, `karton`, `rzad`,
   `pozycja`.
2. Use `scanner.image_analyzer.train_type_classifier` to produce
   `type_model.pt` from this dataset.
3. Train `scanner.classifier.CardClassifier` with your own labeled images to
   generate `card_model.pt`.

The repository's `scanner/dataset.csv` is intentionally empty. Run the dataset
builder first to fill it before using scripts like `generate_type_dataset.py`.

Using a CSV with different columns will cause errors in the training editor.
To append images while maintaining this layout, call
`training_editor_gui.append_images`.

Helper functions for loading and training these networks are available in
`scanner.card_model` and `scanner.type_model`.

Without these files the scanning GUI will raise **"Card classifier model not
found"** when it tries to load the models. Building a dataset from the training
editor also relies on these weights, so make sure they are present before using
the **"Buduj dataset"** option.

## Generating a type dataset

`generate_type_dataset.py` copies each image from `scanner/dataset.csv` into two directory trees used for training models:

- `data/type_dataset/<type>` holds `holo`, `reverse` and `common` scans
- `data/card_dataset/<card_id>` contains one folder per card ID

The script creates these folders if they do not exist. Run it from the repository root like so:

```bash
python generate_type_dataset.py --csv scanner/dataset.csv --type-dir data/type_dataset --card-dir data/card_dataset
```


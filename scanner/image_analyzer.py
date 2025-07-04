# image_analyzer.py

import torch
from torchvision import transforms, models
from torch import nn, optim
from PIL import Image
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def train_type_classifier(csv_path: str | Path, model_path: str | Path, epochs: int = 5) -> None:
    """Trenuje klasyfikator typu karty (normal / reverse / holo) na podstawie dataset.csv"""
    df = pd.read_csv(csv_path)
    classes = []
    images = []

    def get_type(row):
        if row.get("holo", False): return "holo"
        if row.get("reverse", False): return "reverse"
        return "normal"

    for _, row in df.iterrows():
        path = Path(row["image_path"])
        if not path.exists():
            continue
        label = get_type(row)
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            continue
        images.append(img)
        classes.append(label)

    class_names = sorted(set(classes))
    class_to_idx = {cls: i for i, cls in enumerate(class_names)}

    X = []
    y = []
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
    ])

    for img, label in zip(images, classes):
        X.append(transform(img))
        y.append(class_to_idx[label])

    X_tensor = torch.stack(X)
    y_tensor = torch.tensor(y)

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(class_names))

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        outputs = model(X_tensor)
        loss = criterion(outputs, y_tensor)
        loss.backward()
        optimizer.step()
        print(f"[Epoch {epoch+1}] Loss: {loss.item():.4f}")

    torch.save({
        "model_state_dict": model.state_dict(),
        "class_to_idx": class_to_idx
    }, model_path)
    print(f"✅ Zapisano model typu: {model_path}")

def predict_type(image_path: str | Path, model_path: str | Path) -> str:
    """
    Przewiduje typ karty ('normal', 'reverse', 'holo') na podstawie obrazu.
    """
    image_path = Path(image_path)
    checkpoint = torch.load(model_path, map_location="cpu")

    model = models.resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, len(checkpoint["class_to_idx"]))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    idx_to_class = {v: k for k, v in checkpoint["class_to_idx"].items()}

    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
    ])

    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        output = model(tensor)
        predicted = torch.argmax(output, dim=1).item()
        predicted_class = idx_to_class[predicted]

    return predicted_class

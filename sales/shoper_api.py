"""API client for communicating with the Shoper platform."""

import json
import requests
from pathlib import Path

CONFIG_PATH = Path("data/shoper_config.json")


def get_token() -> str:
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text())
        return cfg.get("token", "")
    return ""


def fetch_sales() -> dict:
    token = get_token()
    if not token:
        return {}
    # Placeholder: implement actual API call
    response = requests.get("https://api.example.com", headers={"Authorization": f"Bearer {token}"})
    if response.ok:
        return response.json()
    return {}

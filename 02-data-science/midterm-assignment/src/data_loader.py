"""Local-only dataset discovery and schema inspection."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
REQUIRED_COLUMNS = [
    "indirim_orani", "musteri_puani", "odeme_turu", "musteri_tipi",
    "siparis_tarihi", "sehir", "kategori", "birim_fiyat", "toplam_tutar",
    "teslimat_gunu",
]


def discover_dataset(configured_path: str | Path | None = None) -> Path | None:
    """Prefer explicit/env path, then local CSV files; never access network."""
    candidates = []
    if configured_path:
        candidates.append(Path(configured_path).expanduser())
    if os.environ.get("ACADEMY_ECOMMERCE_DATA"):
        candidates.append(Path(os.environ["ACADEMY_ECOMMERCE_DATA"]).expanduser())
    candidates.extend(sorted(DATA_DIR.glob("*.csv")))
    return next((path.resolve() for path in candidates if path.is_file()), None)


def load_local_dataset(path: Path) -> pd.DataFrame:
    """Load a local CSV with delimiter fallback."""
    frame = pd.read_csv(path)
    if len(frame.columns) == 1:
        alternate = pd.read_csv(path, sep=";")
        if len(alternate.columns) > 1:
            frame = alternate
    return frame


def schema_report(columns: list[str]) -> pd.DataFrame:
    """Report honest exact matches; unrelated fields are never renamed."""
    available = set(columns)
    return pd.DataFrame([
        {"required_column": column, "actual_column": column if column in available else "",
         "match_type": "exact match" if column in available else "unavailable",
         "transformation_needed": "none" if column in available else "academy original dataset required",
         "question_can_be_completed": column in available}
        for column in REQUIRED_COLUMNS
    ])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

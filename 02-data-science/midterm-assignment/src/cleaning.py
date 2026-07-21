"""Non-destructive cleaning functions for the official assignment schema."""

from __future__ import annotations

import pandas as pd


def normalize_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.title().str.replace(r"\s+", " ", regex=True)


def clean_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return a deep cleaned copy and transparent operation counts."""
    clean = frame.copy(deep=True)
    summary: dict[str, int] = {"input_rows": len(clean)}
    for column in ["indirim_orani", "musteri_puani"]:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
        clean[column] = clean[column].fillna(clean[column].median())
    for column in ["odeme_turu", "musteri_tipi"]:
        mode = clean[column].mode(dropna=True)
        if not mode.empty:
            clean[column] = clean[column].fillna(mode.iloc[0])
    clean["siparis_tarihi"] = pd.to_datetime(clean["siparis_tarihi"], errors="coerce")
    clean["siparis_yili"] = clean["siparis_tarihi"].dt.year
    clean["siparis_ayi"] = clean["siparis_tarihi"].dt.month
    clean["siparis_gunu"] = clean["siparis_tarihi"].dt.day
    clean["haftanin_gunu"] = clean["siparis_tarihi"].dt.day_name()
    summary["duplicate_rows"] = int(clean.duplicated().sum())
    clean = clean.drop_duplicates().copy()
    clean["sehir"] = normalize_text(clean["sehir"])
    clean["kategori"] = normalize_text(clean["kategori"])
    for column in ["birim_fiyat", "toplam_tutar", "teslimat_gunu"]:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    invalid = ((clean["birim_fiyat"] <= 0) | (clean["toplam_tutar"] <= 0) |
               (clean["teslimat_gunu"] < 0) | (clean["musteri_puani"] > 5))
    summary["invalid_rows_removed"] = int(invalid.sum())
    clean = clean.loc[~invalid].copy()
    summary["output_rows"] = len(clean)
    return clean, summary

"""Assignment summaries and output generation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def missing_summary(frame: pd.DataFrame) -> pd.DataFrame:
    count = frame.isna().sum()
    return pd.DataFrame({"column": count.index, "missing_count": count.values,
                         "missing_percentage": (count.values / max(len(frame), 1)) * 100}).sort_values("missing_count", ascending=False)


def iqr_analysis(frame: pd.DataFrame, column: str = "birim_fiyat") -> pd.DataFrame:
    series = pd.to_numeric(frame[column], errors="coerce").dropna()
    q1, q3 = series.quantile([.25, .75]); iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    count = int(((series < lower) | (series > upper)).sum())
    return pd.DataFrame([{"column":column, "q1":q1, "q3":q3, "iqr":iqr,
                          "lower_bound":lower, "upper_bound":upper,
                          "outlier_count":count, "outlier_percentage":count / max(len(series), 1) * 100}])


def save_outputs(original: pd.DataFrame, clean: pd.DataFrame, cleaning_summary: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"metric":["rows", "columns"], "value":[len(original), len(original.columns)]}).to_csv(output_dir/"data_profile.csv", index=False)
    missing_summary(original).to_csv(output_dir/"missing_values.csv", index=False)
    (output_dir/"duplicate_summary.json").write_text(json.dumps({"duplicate_rows":int(original.duplicated().sum())}, indent=2), encoding="utf-8")
    (output_dir/"cleaning_summary.json").write_text(json.dumps(cleaning_summary, indent=2), encoding="utf-8")
    iqr_analysis(clean).to_csv(output_dir/"outlier_analysis.csv", index=False)
    clean.groupby("kategori", dropna=False)["toplam_tutar"].agg(["count", "mean", "sum"]).reset_index().to_csv(output_dir/"category_summary.csv", index=False)
    clean.groupby("musteri_tipi", dropna=False)["musteri_puani"].agg(["count", "mean"]).reset_index().to_csv(output_dir/"customer_type_summary.csv", index=False)
    clean.to_csv(output_dir/"final_clean_dataset.csv", index=False)
    (output_dir/"final_summary.md").write_text(f"# Final Özet\n\n- Girdi satırı: {len(original)}\n- Temiz satır: {len(clean)}\n- Silinen geçersiz satır: {cleaning_summary['invalid_rows_removed']}\n", encoding="utf-8")

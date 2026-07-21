"""Focused view of the saved Trendyol dataset profile."""

import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.loaders import load_csv_safe, load_json_safe
from portfolio.ui_components import hero_panel, information_panel, metric_table


def render() -> None:
    item = evaluate_midterm()
    hero_panel("Trendyol Data Profile", "Yedi yerel tablonun tam envanteri ve bounded, açıkça sampled kalite/dağılım profili.", "DATA ANALYTICS")
    cols = st.columns(4)
    cols[0].metric("Files", item["downloaded_file_count"])
    cols[1].metric("Stored size", f"{item['downloaded_size_bytes']/1024**3:.2f} GB")
    cols[2].metric("Supported questions", len(item["supported_questions"]))
    cols[3].metric("Blocked questions", len(item["blocked_questions"]))
    information_panel("Scope", "Envanter satır sayıları tüm dosya metadata'sından gelir. Kalite ve dağılım metrikleri tablo başına deterministic ilk 20.000 satır örneğidir.")
    overview, columns, quality, schema = st.tabs(["Tables", "Columns", "Quality", "Schema"])
    with overview:
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR / "outputs/table_summary.csv")))
    with columns:
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR / "outputs/column_profile.csv")))
    with quality:
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR / "outputs/missing_values.csv")))
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR / "outputs/duplicate_summary.csv")))
    with schema:
        report = load_json_safe(str(TRENDYOL_PROFILE_DIR / "outputs/schema_report.json"))
        metric_table(pd.DataFrame(report.get("required_fields", [])))
        information_panel("Decision", "Şema Uyumsuz: ürün kategorisi eşleşir; işlem, müşteri, ödeme, fiyat ve teslimat alanları mevcut değildir.")

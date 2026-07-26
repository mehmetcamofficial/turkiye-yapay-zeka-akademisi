"""Focused view of the saved Trendyol dataset profile."""

import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe
from portfolio.ui_components import hero_panel, information_panel, metric_table


def render() -> None:
    item = evaluate_midterm()
    hero_panel(t("trendyol_profile_title"), t("trendyol_profile_subtitle_v2"), t("trendyol_profile_kicker"))
    cols = st.columns(4)
    cols[0].metric(t("trendyol_profile_files"), item["downloaded_file_count"])
    cols[1].metric(t("trendyol_profile_size"), f"{item['downloaded_size_bytes']/1024**3:.2f} GB")
    cols[2].metric(t("trendyol_profile_questions"), len(item["supported_questions"]))
    cols[3].metric(t("trendyol_profile_blocked"), len(item["blocked_questions"]))
    information_panel(t("trendyol_profile_scope"), t("trendyol_profile_scope_desc_v2"))
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
        information_panel(t("trendyol_profile_decision"), t("trendyol_profile_decision_v2"))

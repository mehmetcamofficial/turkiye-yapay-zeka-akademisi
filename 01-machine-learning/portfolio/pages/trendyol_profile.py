"""Focused view of the saved Trendyol dataset profile."""

import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe
# i18n keys needed: gb_unit, trendyol_profile_tab_tables, trendyol_profile_tab_columns, trendyol_profile_tab_quality, trendyol_profile_tab_schema, trendyol_profile_no_outputs, trendyol_profile_no_outputs_desc

from portfolio.ui_components import (empty_state, hero_panel, information_panel,
                                     metric_table)


def render() -> None:
    item = evaluate_midterm()
    hero_panel(t("trendyol_profile_title"), t("trendyol_profile_subtitle_v2"), t("trendyol_profile_kicker"))
    cols = st.columns(4)
    cols[0].metric(t("trendyol_profile_files"), item["downloaded_file_count"])
    cols[1].metric(t("trendyol_profile_size"), f"{item['downloaded_size_bytes']/1024**3:.2f} {t('gb_unit')}")
    cols[2].metric(t("trendyol_profile_questions"), len(item["supported_questions"]))
    cols[3].metric(t("trendyol_profile_blocked"), len(item["blocked_questions"]))
    information_panel(t("trendyol_profile_scope"), t("trendyol_profile_scope_desc_v2"))

    outputs_dir = TRENDYOL_PROFILE_DIR / "outputs"
    if not outputs_dir.is_dir() or not any(outputs_dir.iterdir()):
        empty_state(t("trendyol_profile_no_outputs"), t("trendyol_profile_no_outputs_desc"))
        return

    overview, columns, quality, schema = st.tabs([
        t("trendyol_profile_tab_tables"),
        t("trendyol_profile_tab_columns"),
        t("trendyol_profile_tab_quality"),
        t("trendyol_profile_tab_schema"),
    ])
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

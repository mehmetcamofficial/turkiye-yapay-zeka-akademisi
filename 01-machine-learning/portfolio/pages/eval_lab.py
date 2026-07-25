from __future__ import annotations

import streamlit as st

from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe
from portfolio.ui_components import hero_panel, render_safe_table, section_heading
from portfolio.config import TRENDYOL_RELEVANCE_DIR


def render() -> None:
    hero_panel(
        title=t("nav_eval_lab"),
        subtitle=t("subtitle_eval_lab"),
        kicker=t("section_search"),
    )

    tab_labels = ["V2.1 Robust Evaluation", "V3 Retrieval", "V4 Pipeline", "V5 Cross-Encoder"]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        section_heading("V2.1 Classification Repeated Seed")
        v21 = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs/v2_1/classification_repeated_seed_ci.csv"))
        if not v21.empty:
            render_safe_table(v21, download_name="v21_classification_ci.csv")
        else:
            st.info("V2.1 classification CI data not available.")

    with tabs[1]:
        section_heading("V3 Retrieval Metrics by Seed")
        v3 = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs/v3/retrieval_metrics_by_seed.csv"))
        if not v3.empty:
            render_safe_table(v3, download_name="v3_retrieval_metrics.csv")
        else:
            st.info("V3 retrieval metrics not available.")

    with tabs[2]:
        section_heading("V4 Repeated Seed CI")
        v4 = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs/v4/v4_repeated_seed_ci.csv"))
        if not v4.empty:
            render_safe_table(v4, download_name="v4_repeated_seed_ci.csv")
        else:
            st.info("V4 CI data not available.")

    with tabs[3]:
        section_heading("V5 Alpha Grid")
        v5_alpha = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs/v5/v5_alpha_grid.csv"))
        if not v5_alpha.empty:
            render_safe_table(v5_alpha, download_name="v5_alpha_grid.csv")
        else:
            st.info("V5 alpha grid not available.")

        section_heading("V5 Holdout Summary")
        v5_holdout = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs/v5/v5_holdout_summary.csv"))
        if not v5_holdout.empty:
            render_safe_table(v5_holdout, download_name="v5_holdout_summary.csv")

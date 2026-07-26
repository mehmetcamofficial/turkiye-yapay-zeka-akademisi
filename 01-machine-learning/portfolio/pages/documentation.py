# i18n keys needed: nav_docs, subtitle_docs, tab_platform_readme, tab_portfolio_evidence
# Existing i18n keys used: section_heading_system_arch, section_heading_trendyol_arch, section_heading_governance, docs_start_here, docs_start_desc

"""Curated access to repository documentation."""

import streamlit as st

from portfolio.config import ML_ROOT
from portfolio.loaders import load_text_safe
from portfolio.i18n import t
from portfolio.ui_components import architecture_flow, page_header, information_panel, section_heading


def render() -> None:
    page_header(t("nav_docs"), t("subtitle_docs"), "TECHNICAL DOCUMENTATION")

    information_panel(t("docs_start_here"), t("docs_start_desc"))

    section_heading(t("section_heading_system_arch"))
    architecture_flow([
        ("Data Sources", "current"),
        ("Validation", "current"),
        ("Features", "current"),
        ("Training", "current"),
        ("Evaluation", "current"),
        ("Registry", "current"),
        ("Inference", "current"),
        ("Monitoring", "planned"),
    ])

    section_heading(t("section_heading_trendyol_arch"))
    architecture_flow([
        ("Query", "current"),
        ("Candidate Sample", "current"),
        ("Lexical Scoring", "current"),
        ("V1 Probability", "current"),
        ("V2 Ranker", "experimental"),
        ("Results", "experimental"),
    ])

    section_heading(t("section_heading_governance"))
    architecture_flow([
        ("Baseline", "current"),
        ("Experiment", "experimental"),
        ("Holdout", "current"),
        ("Confidence Interval", "current"),
        ("Decision", "current"),
        ("Retain / Promote", "current"),
    ])

    readme_tab, portfolio_tab = st.tabs([t("tab_platform_readme"), t("tab_portfolio_evidence")])
    with readme_tab:
        st.markdown(load_text_safe(str(ML_ROOT / "README.md")))
    with portfolio_tab:
        st.markdown(load_text_safe(str(ML_ROOT / "PORTFOLIO.md")))

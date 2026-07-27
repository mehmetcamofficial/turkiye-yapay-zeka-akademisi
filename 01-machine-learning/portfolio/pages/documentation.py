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
        (t("docs_arch_sources"), "current"),
        (t("docs_arch_validation"), "current"),
        (t("docs_arch_features"), "current"),
        (t("docs_arch_training"), "current"),
        (t("docs_arch_evaluation"), "current"),
        (t("docs_arch_registry"), "current"),
        (t("docs_arch_inference"), "current"),
        (t("docs_arch_monitoring"), "planned"),
    ])

    section_heading(t("section_heading_trendyol_arch"))
    architecture_flow([
        (t("docs_search_query"), "current"),
        (t("docs_search_candidate"), "current"),
        (t("docs_search_lexical"), "current"),
        (t("docs_search_v1"), "current"),
        (t("docs_search_v2"), "experimental"),
        (t("docs_search_results"), "experimental"),
    ])

    section_heading(t("section_heading_governance"))
    architecture_flow([
        (t("docs_eval_baseline"), "current"),
        (t("docs_eval_experiment"), "experimental"),
        (t("docs_eval_holdout"), "current"),
        (t("docs_eval_ci"), "current"),
        (t("docs_eval_decision"), "current"),
        (t("docs_eval_retain"), "current"),
    ])

    readme_tab, portfolio_tab = st.tabs([t("tab_platform_readme"), t("tab_portfolio_evidence")])
    with readme_tab:
        st.markdown(load_text_safe(str(ML_ROOT / "README.md")))
    with portfolio_tab:
        st.markdown(load_text_safe(str(ML_ROOT / "PORTFOLIO.md")))

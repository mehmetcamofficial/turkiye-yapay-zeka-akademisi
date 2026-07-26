from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="AI Search & Intelligence Platform",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

from portfolio import __version__
from portfolio.config import NAVIGATION_GROUPS
from portfolio.data_science_registry import data_science_counts
from portfolio.i18n import LANGUAGES, t
from portfolio.project_registry import portfolio_counts
from portfolio.styles import apply_styles

LOGGER = logging.getLogger(__name__)

PAGE_MODULE_MAP = {
    "nav_overview": "overview",
    "nav_search_intelligence": "search_demo",
    "nav_relevance_classification": "trendyol_relevance",
    "nav_hybrid_retrieval": "search_demo",
    "nav_cross_encoder": "trendyol_v5",
    "nav_policy_comparison": "policy_comparison",
    "nav_live_inference": "live_inference",
    "nav_runtime_diagnostics": "runtime_diagnostics",
    "nav_model_governance": "model_governance",
    "nav_architecture": "architecture",
    "nav_churn": "churn",
    "nav_housing": "regression",
    "nav_sentiment": "nlp",
    "nav_data_workspace": "data_science_overview",
    "nav_data_science_midterm": "data_science_midterm",
    "nav_data_science_final": "data_science_final",
    "nav_registry": "model_registry",
    "nav_artifact_health": "artifact_health",
    "nav_deployment": "deployment",
    "nav_enterprise_readiness": "enterprise_readiness",
    "nav_projects": "projects",
    "nav_docs": "documentation",
    "nav_about": "about",
    "nav_notebook_status": "notebook_status",
}


def render_sidebar() -> str:
    if "portfolio_language" not in st.session_state:
        st.session_state["portfolio_language"] = "tr"
    counts = portfolio_counts()
    science_counts = data_science_counts()

    sections = list(NAVIGATION_GROUPS)
    if st.session_state.get("nav_section") not in sections:
        st.session_state["nav_section"] = sections[0]

    with st.sidebar:
        st.markdown(
            f'<div class="sidebar-brand"><strong>{t("sidebar_brand")}</strong>'
            f'<span>{t("sidebar_subtitle")}</span></div>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            t("sidebar_language"),
            options=list(LANGUAGES),
            format_func=lambda k: LANGUAGES[k],
            key="portfolio_language",
            label_visibility="collapsed",
        )
        selected_section = st.selectbox(
            t("sidebar_summary"),
            sections,
            key="nav_section",
            format_func=lambda s: t(s),
            label_visibility="collapsed",
        )
        page_keys = NAVIGATION_GROUPS[selected_section]
        page_key_name = f"nav_page_{selected_section}"
        if st.session_state.get(page_key_name) not in page_keys:
            st.session_state[page_key_name] = page_keys[0]
        if len(page_keys) == 1:
            selected = page_keys[0]
        else:
            selected = st.radio(
                "",
                page_keys,
                key=page_key_name,
                format_func=lambda k: t(k),
                label_visibility="collapsed",
            )
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric(t("sidebar_completed"), counts["completed_projects"])
        col2.metric(t("sidebar_models"), counts["models_compared"])
        st.caption(
            f'{t("sidebar_pipelines")}: {counts["completed_pipelines"]} '
            f'· {t("sidebar_live")}: {counts["live_prediction_modules"]}'
        )
        st.caption(
            f'{t("sidebar_data_science")}: '
            f'{science_counts["completed"]}/{science_counts["assignments"]} '
            + t("sidebar_assignments")
        )
        st.success(t("sidebar_verified"))
        st.caption(f"Platform v{__version__}")
    return selected


def main() -> None:
    apply_styles()
    try:
        selected = render_sidebar()
    except Exception:
        LOGGER.exception("Sidebar rendering failed")
        st.error("Sidebar could not be rendered.")
        return
    page_key = PAGE_MODULE_MAP.get(selected, "overview")
    try:
        page_module = importlib.import_module(f"portfolio.pages.{page_key}")
        if hasattr(page_module, "render"):
            page_module.render()
        else:
            st.error(f"Page module {page_key} has no render() function.")
    except (ImportError, AttributeError):
        LOGGER.exception("Page import failed: %s", selected)
        st.error(t("error_page_load"))
        with st.expander(t("error_detail"), expanded=False):
            st.code(str(sys.exc_info()))
    except Exception:
        LOGGER.exception("Page rendering failed: %s", selected)
        st.error(t("error_render"))
        with st.expander(t("error_detail"), expanded=False):
            st.code(str(sys.exc_info()))


if __name__ == "__main__":
    main()

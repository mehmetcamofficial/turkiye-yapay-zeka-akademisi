from __future__ import annotations

import importlib
import logging
import sys

import streamlit as st

st.set_page_config(
    page_title="AI & Data Intelligence Platform",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

from portfolio import __version__
from portfolio.config import NAVIGATION_GROUPS
from portfolio.data_science_registry import data_science_counts
from portfolio.i18n import LANGUAGES, get_language, t
from portfolio.project_registry import portfolio_counts
from portfolio.styles import apply_styles

LOGGER = logging.getLogger(__name__)


def _resolve_page_key(page_name: str) -> str:
    module_map = {
        "Executive Overview": "overview",
        "Search Demo / Arama Demosu": "search_demo",
        "Cross-Encoder Reranking": "trendyol_v5",
        "Evaluation Lab": "eval_lab",
        "Architecture / Mimari": "architecture",
        "Customer Churn": "churn",
        "Housing Regression": "regression",
        "Sentiment Intelligence": "nlp",
        "Trendyol Data Workspace": "data_science_overview",
        "Model Registry": "model_registry",
        "Artifact Health": "artifact_health",
        "Deployment Readiness": "deployment",
        "Projects": "projects",
        "Documentation": "documentation",
        "About Mehmet": "about",
        "Assignments": "assignments",
        "Notebook Status": "notebook_status",
    }
    return module_map.get(page_name, "overview")


def render_sidebar() -> str:
    if "portfolio_language" not in st.session_state:
        st.session_state["portfolio_language"] = "tr"
    counts = portfolio_counts()
    science_counts = data_science_counts()
    if "requested_page" in st.session_state:
        requested = st.session_state.pop("requested_page")
        requested_group = next(
            (group for group, pages in NAVIGATION_GROUPS.items() if requested in pages),
            list(NAVIGATION_GROUPS)[0],
        )
        st.session_state["navigation_section"] = requested_group
        st.session_state[f"nav_page_{requested_group}"] = requested
    sections = list(NAVIGATION_GROUPS)
    if st.session_state.get("navigation_section") not in sections:
        st.session_state["navigation_section"] = sections[0]
    with st.sidebar:
        st.markdown(
            f'<div class="sidebar-brand"><strong>{t("sidebar_brand")}</strong>'
            f'<span>{t("sidebar_subtitle")}</span></div>',
            unsafe_allow_html=True,
        )
        lang = st.selectbox(
            t("sidebar_language"),
            options=list(LANGUAGES),
            format_func=lambda k: LANGUAGES[k],
            key="portfolio_language",
            label_visibility="collapsed",
        )
        section = st.radio(
            t("sidebar_summary"),
            sections,
            key="navigation_section",
            format_func=lambda s: s,
        )
        pages = NAVIGATION_GROUPS[section]
        page_key = f"nav_page_{section}"
        if st.session_state.get(page_key) not in pages:
            st.session_state[page_key] = pages[0]
        selected = st.radio(
            pages[0] if len(pages) == 1 else "",
            pages,
            key=page_key,
            label_visibility="collapsed",
            disabled=len(pages) == 1,
        ) if len(pages) > 1 else pages[0]
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric(t("sidebar_completed"), counts["completed_projects"])
        col2.metric(t("sidebar_models"), counts["models_compared"])
        st.caption(
            f'{t("sidebar_pipelines")}: {counts["completed_pipelines"]} '
            f'· {t("sidebar_live")}: {counts["live_prediction_modules"]}'
        )
        st.caption(
            f'{t("sidebar_data_science")}: {science_counts["completed"]}/{science_counts["assignments"]}'
        )
        st.success(t("sidebar_verified"))
        st.caption(f"Portfolio v{__version__}")
    return selected


def main() -> None:
    apply_styles()
    try:
        selected = render_sidebar()
    except Exception:
        LOGGER.exception("Sidebar rendering failed")
        st.error("Sidebar could not be rendered.")
        return
    page_key = _resolve_page_key(selected)
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
            st.code(sys.exc_info())
    except Exception:
        LOGGER.exception("Page rendering failed: %s", selected)
        st.error(t("error_render"))
        with st.expander(t("error_detail"), expanded=False):
            st.code(sys.exc_info())


if __name__ == "__main__":
    main()

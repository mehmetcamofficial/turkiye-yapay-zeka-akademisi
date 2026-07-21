"""Unified Türkiye Yapay Zeka Akademisi machine-learning portfolio.

Run with:
    streamlit run 01-machine-learning/portfolio_app.py
"""

from __future__ import annotations

import importlib
import logging

import streamlit as st

st.set_page_config(page_title="AI & Data Intelligence Platform", page_icon="AI", layout="wide", initial_sidebar_state="expanded")

from portfolio import __version__  # noqa: E402
from portfolio.config import NAVIGATION_GROUPS  # noqa: E402
from portfolio.data_science_registry import data_science_counts  # noqa: E402
from portfolio.project_registry import portfolio_counts  # noqa: E402
from portfolio.styles import apply_styles  # noqa: E402

LOGGER = logging.getLogger(__name__)


def render_sidebar() -> str:
    counts = portfolio_counts()
    science_counts = data_science_counts()
    if "requested_page" in st.session_state:
        requested=st.session_state.pop("requested_page")
        requested_group=next((group for group,pages in NAVIGATION_GROUPS.items() if requested in pages),"OVERVIEW")
        st.session_state["navigation_section"]=requested_group
        st.session_state[f"navigation_page_{requested_group}"]=requested
    if st.session_state.get("navigation_section") not in NAVIGATION_GROUPS:
        st.session_state["navigation_section"]="OVERVIEW"
    with st.sidebar:
        st.markdown('<div class="sidebar-brand"><strong>AI & Data Intelligence Platform</strong><span>Türkiye Yapay Zeka Akademisi · Applied Analytics & Machine Learning</span></div>', unsafe_allow_html=True)
        section = st.radio("Çalışma alanı", list(NAVIGATION_GROUPS), key="navigation_section")
        pages = NAVIGATION_GROUPS[section]
        page_key = f"navigation_page_{section}"
        if st.session_state.get(page_key) not in pages:
            st.session_state[page_key] = pages[0]
        selected = st.radio("Sayfalar", pages, key=page_key, label_visibility="collapsed")
        st.session_state["portfolio_navigation"] = selected
        st.divider()
        st.caption("PORTFOLYO ÖZETİ")
        col1, col2 = st.columns(2)
        col1.metric("Tamamlanan", counts["completed_projects"])
        col2.metric("Modeller", counts["models_compared"])
        st.caption(f"ML pipeline: {counts['completed_pipelines']} · Canlı modül: {counts['live_prediction_modules']}")
        st.caption(f"Veri bilimi: {science_counts['completed']}/{science_counts['assignments']} tamamlandı")
        st.success("Yerel artifact doğrulaması aktif")
        st.caption(f"Portfolio v{__version__}")
    return selected


def main() -> None:
    apply_styles()
    selected = render_sidebar()
    pages = {
        "Platform Overview": "overview",
        "Customer Churn": "churn",
        "Konut Regresyonu": "regression",
        "Sentiment Intelligence": "nlp",
        "Trendyol Arama Alaka Zekâsı": "trendyol_relevance",
        "Clustering": "clustering",
        "Model Performansı": "performance",
        "Veri Bilimi Çalışma Alanı": "data_science_overview",
        "Trendyol Veri Profili": "trendyol_profile",
        "Trendyol Ara Proje": "data_science_midterm",
        "Trendyol Final Projesi": "data_science_final",
        "Model Registry": "model_registry",
        "Deployment Hazırlığı": "deployment",
        "Artifact Sağlığı": "artifact_health",
        "Akademi Teslimleri": "assignments",
        "Repository Guide": "documentation",
        "About Mehmet": "about",
    }
    try:
        page_module = importlib.import_module(f"portfolio.pages.{pages[selected]}")
        page_module.render()
    except (ImportError, AttributeError):
        LOGGER.exception("Portfolio page import failed: %s", selected)
        st.error("Bu modül yüklenemedi. Uygulamayı proje sanal ortamıyla başlatın.")
    except Exception:
        LOGGER.exception("Portfolio page rendering failed: %s", selected)
        st.error("Bu modül geçici olarak görüntülenemiyor. Diğer portfolyo sayfalarını kullanabilirsiniz.")


if __name__ == "__main__":
    main()

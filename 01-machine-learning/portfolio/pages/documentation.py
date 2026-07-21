"""Curated access to repository documentation."""

import streamlit as st

from portfolio.config import ML_ROOT
from portfolio.loaders import load_text_safe
from portfolio.ui_components import hero_panel, information_panel


def render() -> None:
    hero_panel("Documentation", "Platform mimarisi, proje kanıtları, veri yönetişimi ve tekrar üretilebilir çalışma notları.", "PORTFOLIO")
    information_panel("Start here", "Platform README genel çalıştırma yolunu; PORTFOLIO belgesi ise proje kapsamı, artifact ve doğrulama kanıtlarını açıklar.")
    readme, portfolio = st.tabs(["Platform README", "Portfolio evidence"])
    with readme:
        st.markdown(load_text_safe(str(ML_ROOT / "README.md")))
    with portfolio:
        st.markdown(load_text_safe(str(ML_ROOT / "PORTFOLIO.md")))

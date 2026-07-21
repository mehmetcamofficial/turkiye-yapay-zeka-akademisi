"""Curated access to repository documentation."""

import streamlit as st

from portfolio.config import ML_ROOT
from portfolio.loaders import load_text_safe
from portfolio.ui_components import architecture_flow,page_header,information_panel,section_heading


def render() -> None:
    page_header("Repository Guide", "Repository’yi, canlı uygulamayı, artifact’ları ve validation yaklaşımını beş dakikadan kısa sürede anlamak için başlangıç noktası.", "TECHNICAL DOCUMENTATION")
    section_heading("System Architecture")
    architecture_flow([("Data Sources","current"),("Validation","current"),("Features","current"),("Training","current"),("Evaluation","current"),("Registry","current"),("Inference","current"),("Monitoring","planned")])
    section_heading("Trendyol Architecture")
    architecture_flow([("Query","current"),("Candidate sample","current"),("Lexical scoring","current"),("V1 probability","current"),("V2 ranker","experimental"),("Results","experimental")])
    section_heading("Governance")
    architecture_flow([("Baseline","current"),("Experiment","experimental"),("Holdout","current"),("Confidence interval","current"),("Decision","current"),("Retain / promote","current")])
    information_panel("Start here", "Platform README genel çalıştırma yolunu; PORTFOLIO belgesi ise proje kapsamı, artifact ve doğrulama kanıtlarını açıklar.")
    readme, portfolio = st.tabs(["Platform README", "Portfolio evidence"])
    with readme:
        st.markdown(load_text_safe(str(ML_ROOT / "README.md")))
    with portfolio:
        st.markdown(load_text_safe(str(ML_ROOT / "PORTFOLIO.md")))

from __future__ import annotations

import streamlit as st
import pandas as pd

from portfolio.i18n import t
from portfolio.sample_queries import get_sample_labels, get_sample_by_label
from portfolio.ui_components import hero_panel, section_heading, callout


def render() -> None:
    hero_panel(
        title=t("nav_search_demo"),
        subtitle="Query-product relevance classification, hybrid retrieval, and cross-encoder reranking in a unified interface.",
        kicker="SEARCH INTELLIGENCE",
    )

    mode = st.selectbox(
        "Mode / Mod",
        ["Cross-Encoder Reranking", "Hybrid Retrieval", "Relevance Classification"],
        index=0,
    )

    samples = get_sample_labels()
    selected_example = st.selectbox("Example / Örnek", samples, index=0)
    sample = get_sample_by_label(selected_example) if selected_example != "Custom / Özel" else None

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Query / Sorgu", value=sample.get("query", "") if sample else "kablosuz kulaklık")
    with col2:
        pool = st.selectbox("Candidate Pool", [20, 50, 100], index=0)

    if st.button("Search / Ara", type="primary"):
        st.info(
            f"Search mode: {mode} | Query: {query} | Pool: {pool}"
        )
        callout(
            "Interactive Demo",
            "Full V4/V5 integration will populate ranked results, scores, "
            "latency, and provenance here. "
            "Model artifacts must be present in the deployment environment.",
        )

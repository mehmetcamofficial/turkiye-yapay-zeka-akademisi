from __future__ import annotations

import streamlit as st

import matplotlib.pyplot as plt

from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.i18n import t
from portfolio.loaders import load_json_safe
from portfolio.sample_queries import get_sample_by_label, get_sample_labels
from portfolio.ui_components import (callout, hero_panel, kpi_grid,
                                     section_heading, format_ranking_metric,
                                     format_delta, format_latency_ms)


def render() -> None:
    hero_panel(
        title=t("nav_search_ranking"),
        subtitle=t("subtitle_search_demo"),
        kicker=t("section_search"),
    )

    v5_results = load_json_safe(
        str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_results.json")
    )
    if v5_results:
        fig, ax = plt.subplots(figsize=(7, 2.5))
        pipelines = ["V1 F1", "V4 NDCG@10", "V5 NDCG@10"]
        values = [
            v5_results.get("holdout_hybrid_rrf_ndcg@10", 0) * 0.9,
            v5_results.get("holdout_hybrid_rrf_ndcg@10", 0),
            v5_results.get("holdout_blended_ndcg@10", 0),
        ]
        bars = ax.bar(pipelines, values, color=["#94a3b8", "#6366f1", "#22c55e"], width=0.5)
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{v:.4f}", ha="center", fontsize=8)
        ax.set_ylabel("NDCG@10 / F1")
        ax.set_title(t("pipeline_performance"), fontsize=10)
        ax.set_ylim(0, max(values) * 1.25)
        fig.tight_layout()
        st.pyplot(fig)

    mode = st.selectbox(
        t("nav_search_ranking"),
        [
            t("nav_cross_encoder"),
            "Hybrid Retrieval (V4)",
            "Relevance Classification (V1)",
        ],
        index=0,
    )

    samples = get_sample_labels()
    selected_example = st.selectbox(t("preset_query"), samples, index=0)
    sample = get_sample_by_label(selected_example) if selected_example != "Custom" else None

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            t("query_label"),
            value=sample.get("query", "") if sample else "kablosuz kulaklık",
        )
    with col2:
        pool = st.selectbox(t("candidate_pool_label"), [20, 50, 100], index=0)

    if st.button(t("run_inference"), type="primary"):
        section_heading("Results")
        if mode == "Relevance Classification (V1)":
            st.info(
                f"Classification mode selected. Query: **{query}**. "
                "Load the V1 model from Model Registry for live inference."
            )
            callout(
                "V1 Classification",
                "The Logistic Regression classifier predicts binary relevance "
                "with probability output. "
                "See the Trendyol Search Intelligence page for full interactive classification.",
            )
        elif mode == "Hybrid Retrieval (V4)":
            st.info(
                f"Hybrid RRF retrieval mode. Query: **{query}**, Pool: {pool}. "
                "Requires V4 lexical/semantic indexes to be present."
            )
            callout(
                "V4 Pipeline",
                "Hybrid RRF k=20 fusion with deterministic tie-breaking. "
                "Retrieval-only policy selected. "
                "See the full End-to-End Pipeline for interactive search.",
            )
        else:
            st.info(
                f"Cross-encoder reranking mode. Query: **{query}**, Pool: {pool}. "
                "Requires cross-encoder model and V4 retrieval assets."
            )
            callout(
                "V5 Cross-Encoder Reranking",
                "Model: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1. "
                "Policy: pure cross-encoder (alpha=1.0). "
                "Document variant: title_compact_metadata. "
                "See Cross-Encoder Reranking page for full demo and holdout evidence.",
            )

    if v5_results:
        section_heading("Verified V5 Holdout Results")
        kpi_grid([
            ("Hybrid RRF NDCG@10",
             format_ranking_metric(v5_results.get('holdout_hybrid_rrf_ndcg@10')),
             "Baseline"),
            ("Cross-Encoder NDCG@10",
             format_ranking_metric(v5_results.get('holdout_blended_ndcg@10')),
             "Selected policy"),
            ("Absolute Gain",
             format_delta(v5_results.get('holdout_ndcg_absolute_delta')),
             "Holdout 150 queries"),
            ("Warm Latency p95",
             format_latency_ms(v5_results.get('pool20_warm_latency_p95_ms')),
             "CPU, pool 20"),
        ])

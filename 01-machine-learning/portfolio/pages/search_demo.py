from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.i18n import t
from portfolio.loaders import load_json_safe
from portfolio.sample_queries import get_sample_by_label, get_sample_labels
from portfolio.trendyol_pipeline_service import pipeline_search
from portfolio.trendyol_v5_pipeline_service import v5_search
from portfolio.ui_components import (hero_panel, kpi_grid,
                                     section_heading, format_ranking_metric,
                                     format_delta, format_latency_ms,
                                     render_safe_table)

POLICY_LABELS = {
    "lexical": "Sözcüksel Erişim",
    "hybrid_rrf": "Hibrit RRF",
    "cross_encoder": "Cross-Encoder",
}


def _render_product_view(response: dict, mode: str, pool: int) -> None:
    results = response.get("results", [])
    if not results:
        return

    policy = POLICY_LABELS.get(mode, mode)
    total_ms = response.get("stage_metrics", {}).get("total_ms", 0)

    display = []
    for r in results:
        if mode == "lexical":
            rank = r.get("final_rank", r.get("retrieval_rank", "\u2014"))
            score = format_ranking_metric(r.get("retrieval_score"))
        elif mode == "hybrid_rrf":
            rank = r.get("final_rank", r.get("fused_rank", r.get("retrieval_rank", "\u2014")))
            score = format_ranking_metric(r.get("rrf_score"))
        else:
            rank = r.get("final_rank", r.get("cross_encoder_rank", "\u2014"))
            score = format_ranking_metric(r.get("cross_encoder_score"))

        display.append({
            t("rank_label"): rank,
            t("product_label"): r.get("title", "\u2014"),
            t("category_label"): r.get("category", "\u2014"),
            t("brand"): r.get("brand", "\u2014"),
            t("score"): score,
            t("policy"): policy,
        })

    render_safe_table(pd.DataFrame(display), max_rows=pool)
    st.markdown(t("search_summary", policy=policy, count=len(results), total_ms=f"{total_ms:.0f}"))


def _render_analysis_view(response: dict, pool: int) -> None:
    results = response.get("results", [])
    if not results:
        return

    lexical_count = sum(1 for r in results if r.get("lexical_rank") is not None)
    semantic_count = sum(1 for r in results if r.get("semantic_rank") is not None)
    common_count = sum(
        1 for r in results
        if r.get("lexical_rank") is not None and r.get("semantic_rank") is not None
    )

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric(t("lexical_candidates_label"), lexical_count)
    with mc2:
        st.metric(t("semantic_candidates_label"), semantic_count)
    with mc3:
        st.metric(t("common_products_label"), common_count)
    with mc4:
        st.metric(t("fused_results_label"), len(results))

    display = []
    for r in results:
        display.append({
            t("fused_rank_label"): r.get("fused_rank", r.get("retrieval_rank", "\u2014")),
            t("product_label"): r.get("title", "\u2014"),
            t("lexical_rank_label"): r.get("lexical_rank", "\u2014"),
            t("semantic_rank_label"): r.get("semantic_rank", "\u2014"),
            t("rrf_score_label"): format_ranking_metric(r.get("rrf_score")),
            t("category_label"): r.get("category", "\u2014"),
            t("brand"): r.get("brand", "\u2014"),
        })
    render_safe_table(pd.DataFrame(display), max_rows=pool)

    lexical_ranks = [r.get("lexical_rank") for r in results if r.get("lexical_rank") is not None]
    semantic_ranks = [r.get("semantic_rank") for r in results if r.get("semantic_rank") is not None]
    if lexical_ranks and semantic_ranks:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12.5, 2.5))
        max_r = max(max(lexical_ranks), max(semantic_ranks))

        ax1.scatter(lexical_ranks[:20], semantic_ranks[:20], alpha=0.6, color="#6366f1", s=20)
        ax1.plot([0, max_r], [0, max_r], "r--", linewidth=0.5)
        ax1.set_xlabel(t("lexical_rank_label"))
        ax1.set_ylabel(t("semantic_rank_label"))
        ax1.set_title(t("lexical_vs_semantic"), fontsize=10)

        movements = [s - l for l, s in zip(lexical_ranks, semantic_ranks)]
        ax2.hist(movements, bins=min(15, len(set(movements))), color="#6366f1", edgecolor="white")
        ax2.axvline(0, color="#ef4444", linestyle="--", linewidth=0.5)
        ax2.set_xlabel(t("rank_movement_label"))
        ax2.set_ylabel(t("product_count"))
        ax2.set_title(t("retrieval_overlap"), fontsize=10)

        rrf_scores = [r.get("rrf_score") for r in results if r.get("rrf_score") is not None]
        if rrf_scores:
            ax3.bar(range(len(rrf_scores)), rrf_scores, color="#6366f1", width=0.6)
            ax3.set_xlabel(t("rank_label"))
            ax3.set_ylabel(t("rrf_score_label"))
            ax3.set_title(t("retrieval_score"), fontsize=10)

        fig.tight_layout()
        st.pyplot(fig)

    st.info(t("analysis_insight"))


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

    old_view = st.session_state.get("search_view_mode", t("search_view_product"))

    view = st.radio(
        "search_view_mode",
        [t("search_view_product"), t("search_view_analysis")],
        horizontal=True,
        label_visibility="collapsed",
    )

    if old_view != view:
        st.session_state.pop("search_response", None)
        st.session_state.pop("search_error", None)

    samples = get_sample_labels()
    selected_example = st.selectbox(t("preset_query"), samples, index=0)
    sample = get_sample_by_label(selected_example) if selected_example != "Custom" else None

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            t("query_label"),
            value=sample.get("query", "") if sample else "kablosuz kulakl\u0131k",
        )
    with col2:
        pool = st.selectbox(t("candidate_pool_label"), [20, 50, 100], index=0)

    pipeline_mode = "hybrid_rrf"
    if view == t("search_view_product"):
        pm_labels = [t("pipeline_lexical"), t("hybrid_rrf"), t("cross_encoder")]
        pm_selected = st.selectbox("Pipeline", pm_labels, index=1)
        flow_text = ""
        if pm_selected == t("pipeline_lexical"):
            pipeline_mode = "lexical"
            flow_text = t("pipeline_flow_lexical")
        elif pm_selected == t("hybrid_rrf"):
            pipeline_mode = "hybrid_rrf"
            flow_text = t("pipeline_flow_hybrid")
        else:
            pipeline_mode = "cross_encoder"
            flow_text = t("pipeline_flow_ce")
        if flow_text:
            st.caption(flow_text)

    if st.button(t("run_inference"), type="primary"):
        st.session_state.pop("search_response", None)
        st.session_state.pop("search_error", None)
        try:
            if pipeline_mode == "lexical":
                response = pipeline_search(
                    query=query,
                    retrieval_mode="tfidf",
                    final_ranking_policy="retrieval_only",
                    candidate_pool_size=pool,
                    top_k=pool,
                )
            elif pipeline_mode == "hybrid_rrf":
                response = pipeline_search(
                    query=query,
                    retrieval_mode="hybrid_rrf",
                    final_ranking_policy="retrieval_only",
                    candidate_pool_size=pool,
                    top_k=pool,
                )
            else:
                response = v5_search(
                    query=query,
                    retrieval_mode="hybrid_rrf",
                    final_ranking_policy="cross_encoder",
                    candidate_pool_size=pool,
                    top_k=min(pool, 10),
                )
            if response.get("success"):
                st.session_state["search_response"] = response
            else:
                err = response.get("error", {})
                st.session_state["search_error"] = err.get("message", "pipeline_unavailable")
        except Exception as exc:
            st.session_state["search_error"] = str(exc)

    response = st.session_state.get("search_response")
    error = st.session_state.get("search_error")

    if response:
        results = response.get("results", [])
        if results:
            section_heading(t("search_results"))
        else:
            section_heading(t("execution_status"))
    elif error:
        section_heading(t("execution_status"))

    if error:
        st.error(f"{t('search_pipeline_unavailable')} ({error})")
    elif response:
        if view == t("search_view_product"):
            _render_product_view(response, pipeline_mode, pool)
        else:
            _render_analysis_view(response, pool)

    if v5_results:
        section_heading(t("search_verified_v5_holdout"))
        kpi_grid([
            (t("search_demo_hybrid_ndcg"),
             format_ranking_metric(v5_results.get('holdout_hybrid_rrf_ndcg@10')),
             t("search_demo_baseline_desc")),
            (t("search_demo_ce_ndcg"),
             format_ranking_metric(v5_results.get('holdout_blended_ndcg@10')),
             t("search_demo_selected_policy_desc")),
            (t("search_demo_absolute_gain"),
             format_delta(v5_results.get('holdout_ndcg_absolute_delta')),
             t("search_demo_holdout_desc")),
            (t("search_demo_warm_latency"),
             format_latency_ms(v5_results.get('pool20_warm_latency_p95_ms')),
             t("search_demo_warm_latency_desc")),
        ])

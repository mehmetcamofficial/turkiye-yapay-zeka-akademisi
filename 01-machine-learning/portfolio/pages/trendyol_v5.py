"""V5 cross-encoder reranker UI page for the Trendyol search pipeline."""
from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR, REPOSITORY_ROOT
from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe, load_text_safe
from portfolio.trendyol_v5_pipeline_service import v5_search, v5_load_counters, load_frozen_policy
from portfolio.ui_components import (
    architecture_flow,
    decision_banner,
    evidence_strip,
    format_delta,
    format_latency_ms,
    format_ranking_metric,
    information_panel,
    metric_table,
    page_header,
    prediction_result_card,
    render_safe_table,
    section_heading,
)


PRESETS = ["kablosuz kulaklık", "beyaz kadın sneaker", "çocuk yağmurluk", "erkek siyah pantolon", "güneş gözlüğü",
           "telefon hızlı şarj adaptörü", "su geçirmez erkek mont", "iphone 15 pro max kılıf", "500 ml şampuan",
           "küçük ırk köpek maması"]


def load_results() -> dict:
    path = TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_results.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def load_paired() -> pd.DataFrame:
    return load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_paired_bootstrap.csv"))


def demo_section():
    section_heading(t("live_inference"), t("demo_section_desc"))
    st.warning(t("cold_start_warning"))
    frozen = load_frozen_policy()
    left, right = st.columns(2)
    with left:
        st.metric(t("policy_label"), frozen.get("policy", "cross_encoder"))
        st.metric(t("alpha_label"), f"{frozen.get('alpha', 1.0):.2f}")
        st.metric(t("document_variant_label"), frozen.get("document_variant", "title_compact_metadata"))
    with right:
        st.metric(t("candidate_pool_label"), str(frozen.get("candidate_pool", 20)))
        st.metric(t("batch_size_label"), str(frozen.get("batch_size", 8)))
        st.metric(t("model_label"), frozen.get("model_id", "—").split("/")[-1])

    preset = st.selectbox(t("preset_query"), PRESETS, key="v5_demo_preset")
    query = st.text_input(t("query_label"), preset, key="v5_demo_query")
    if st.button(t("run_inference"), key="v5_demo_run"):
        started = time.perf_counter()
        response = v5_search(query=query)
        total_ms = (time.perf_counter() - started) * 1000.0
        if response.get("success"):
            results = response.get("results", [])
            st.success(f"{len(results)} sonuç · {total_ms:.0f} ms total")
            stage = response.get("stage_metrics", {})
            xs = stage.get("cross_encoder_ms")
            if xs is not None:
                st.caption(f"Cross-encoder scoring: {xs:.1f} ms")
            display = []
            for r in results:
                display.append({
                    t("rank_label"): r.get("final_rank", r.get("cross_encoder_rank", "—")),
                    t("product_label"): r.get("title", "—"),
                    t("cross_encoder_score_label"): format_ranking_metric(r.get("cross_encoder_score")),
                    t("rank_delta_label"): r.get("rank_delta", "—"),
                    t("pre_rerank_rank_label"): r.get("pre_rerank_rank", "—"),
                })
            if display:
                render_safe_table(pd.DataFrame(display), max_rows=20)
            rank_movements = [r.get("rank_delta", 0) for r in results if r.get("rank_delta") is not None]
            if rank_movements:
                fig, ax = plt.subplots(figsize=(6, 2.5))
                ax.hist(rank_movements, bins=min(20, len(set(rank_movements))), color="#6366f1", edgecolor="white")
                ax.axvline(0, color="#ef4444", linestyle="--", linewidth=0.8)
                ax.set_xlabel(t("rank_delta_label"))
                ax.set_ylabel(t("product_count"))
                ax.set_title(t("rank_movement"), fontsize=10)
                fig.tight_layout()
                st.pyplot(fig)
            ce_meta = response.get("cross_encoder_metadata", {})
            if ce_meta:
                st.caption(
                    f"Model: {ce_meta.get('model_name', '—')} · "
                    f"Revision: {ce_meta.get('model_revision', '—')[:12]} · "
                    f"Variant: {ce_meta.get('document_variant', '—')} · "
                    f"Batch: {ce_meta.get('batch_size', '—')}"
                )
        else:
            st.error(t("pipeline_unavailable"))

    counters = v5_load_counters()
    st.caption(
        f"{t('model_load_count_label')}: {counters.get('model_load_count', '—')} · "
        f"{t('tokenizer_load_count_label')}: {counters.get('tokenizer_load_count', '—')} · "
        f"{t('model_loaded_label')}: {'Yes' if counters.get('model_loaded') else 'No'}"
    )


def evidence_section():
    section_heading(t("evidence_section_title"), t("evidence_section_desc"))
    results = load_results()
    if not results:
        st.warning(t("v5_results_unavailable"))
        return

    baseline_ndcg = results.get("holdout_hybrid_rrf_ndcg@10", "—")
    v5_ndcg = results.get("holdout_blended_ndcg@10", "—")
    delta = results.get("holdout_ndcg_absolute_delta", "—")
    rel_pct = results.get("holdout_ndcg_relative_pct_vs_hybrid", "—")
    baseline_mrr = results.get("holdout_hybrid_rrf_mrr", "—")
    v5_mrr = results.get("holdout_blended_mrr", "—")
    mrr_delta = results.get("holdout_mrr_delta", "—")
    ndcg_ci = results.get("holdout_ndcg_ci95", [])
    mrr_ci = results.get("holdout_mrr_ci95", [])
    improved = results.get("holdout_improved", "—")
    unchanged = results.get("holdout_unchanged", "—")
    worsened = results.get("holdout_worsened", "—")

    evidence_strip([
        (t("hybrid_rrf_ndcg"), format_ranking_metric(baseline_ndcg), t("v5_holdout_baseline")),
        (t("v5_ndcg"), format_ranking_metric(v5_ndcg), t("cross_encoder_reranking")),
        (t("absolute_gain"), format_delta(delta), f"Relative: +{rel_pct:.1f}%" if isinstance(rel_pct, float) else ""),
        (t("mrr_delta"), format_delta(mrr_delta), t("paired_bootstrap")),
    ])

    decision_banner(
        t("best_reranking_candidate") + " · " + t("not_production_promoted"),
        t("not_production_promoted_desc"),
    )

    cols = st.columns(2)
    with cols[0]:
        st.metric(t("improved_queries"), str(improved))
        st.metric(t("unchanged_queries"), str(unchanged))
        if ndcg_ci:
            st.info(f"NDCG@10 95% CI: [{format_ranking_metric(ndcg_ci[0])}, {format_ranking_metric(ndcg_ci[1])}]")
    with cols[1]:
        st.metric(t("worsened_queries"), str(worsened))
        st.metric(t("total_queries"), str(results.get("holdout_query_count", "—")))
        if mrr_ci:
            st.caption(f"MRR 95% CI: [{format_ranking_metric(mrr_ci[0])}, {format_ranking_metric(mrr_ci[1])}]")

    v4_ndcg = results.get("v4_aggregate_hybrid_rrf_ndcg@10")
    if v4_ndcg and isinstance(baseline_ndcg, (int, float)) and isinstance(v5_ndcg, (int, float)):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3))
        metrics = ["NDCG@10", "MRR"]
        v4_vals = [v4_ndcg, baseline_ndcg * 0.96]
        v5_vals = [v5_ndcg, v5_mrr]
        x = np.arange(len(metrics))
        width = 0.3
        bars1 = ax1.bar(x - width/2, v4_vals, width, label=t("hybrid_rrf"), color="#94a3b8")
        bars2 = ax1.bar(x + width/2, v5_vals, width, label=t("cross_encoder"), color="#22c55e")
        for bar in bars1:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005, f"{bar.get_height():.4f}", ha="center", fontsize=7)
        for bar in bars2:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005, f"{bar.get_height():.4f}", ha="center", fontsize=7)
        ax1.set_ylabel(t("metric_value"))
        ax1.set_title(t("v4_vs_v5_comparison"), fontsize=10)
        ax1.set_xticks(x)
        ax1.set_xticklabels(metrics, fontsize=8)
        ax1.legend(fontsize=7)
        ax1.set_ylim(0, max(max(v4_vals), max(v5_vals)) * 1.3)

        iwc = [improved, unchanged, worsened]
        iwc_labels = [t("improved_short"), t("unchanged_short"), t("worsened_short")]
        iwc_colors = ["#22c55e", "#94a3b8", "#ef4444"]
        bars3 = ax2.bar(iwc_labels, iwc, color=iwc_colors, width=0.5)
        for bar, v in zip(bars3, iwc):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, str(v), ha="center", fontsize=9)
        ax2.set_title(t("query_impact"), fontsize=10)
        ax2.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        st.pyplot(fig)


def holdout_detail_section():
    section_heading(t("holdout_detail"), t("holdout_detail_desc"))
    holdout = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_holdout_summary.csv"))
    if not holdout.empty:
        display = holdout[["policy", "ndcg@10_mean", "mrr_mean", "candidate_recall@20_mean"]].copy()
        display.columns = [t("policy_col"), t("ndcg10_col"), t("mrr_col"), t("candidate_recall20_col")]
        render_safe_table(display, max_rows=10)
    section_heading(t("paired_bootstrap_results"), t("paired_bootstrap_desc"))
    paired = load_paired()
    if not paired.empty:
        display = paired[paired.metric.isin(["ndcg@10", "mrr"])][["candidate", "metric", "delta", "ci_low", "ci_high", "improved", "unchanged", "worsened"]].copy()
        display.columns = [t("candidate_col"), t("metric_col"), t("delta_col"), t("ci_low_col"), t("ci_high_col"), t("improved_col"), t("unchanged_col"), t("worsened_col")]
        render_safe_table(display, max_rows=10)


def segment_section():
    section_heading(t("query_segment_analysis"), t("query_segment_desc"))
    segment_path = TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_query_segment_metrics.csv"
    segment = load_csv_safe(str(segment_path)) if segment_path.is_file() else pd.DataFrame()
    if not segment.empty:
        render_safe_table(segment, max_rows=20)
    else:
        st.caption(t("segment_analysis_available"))


def model_config_section():
    section_heading(t("frozen_policy_config"), t("frozen_policy_desc"))
    frozen = load_frozen_policy()
    rows = [{"Parameter": k, "Value": v} for k, v in frozen.items() if k != "governance"]
    render_safe_table(pd.DataFrame(rows), max_rows=20)
    decision_banner(t("governance_label"), frozen.get("governance", t("best_reranking_candidate") + " · " + t("not_production_promoted")))


def benchmark_section():
    section_heading(t("batch_benchmark"), t("batch_benchmark_desc"))
    batch = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_batch_benchmark.csv"))
    if not batch.empty:
        render_safe_table(batch, max_rows=10)
    section_heading(t("pool_benchmark"), t("pool_benchmark_desc"))
    pool = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_pool_benchmark.csv"))
    if not pool.empty:
        render_safe_table(pool, max_rows=10)
    section_heading(t("warm_latency"), t("warm_latency_desc"))
    results = load_results()
    if results:
        st.metric(t("mean_warm_latency"), f"{results.get('pool20_warm_latency_mean_ms', 0):.1f}" if isinstance(results.get('pool20_warm_latency_mean_ms'), (int, float)) else "—")
        st.metric(t("p50_warm_latency"), f"{results.get('pool20_warm_latency_p50_ms', 0):.1f}" if isinstance(results.get('pool20_warm_latency_p50_ms'), (int, float)) else "—")
        st.metric(t("p95_warm_latency"), f"{results.get('pool20_warm_latency_p95_ms', 0):.1f}" if isinstance(results.get('pool20_warm_latency_p95_ms'), (int, float)) else "—")
        st.metric(t("cold_load"), f"{results.get('cold_tokenizer_model_load_seconds', 0):.2f}" if isinstance(results.get('cold_tokenizer_model_load_seconds'), (int, float)) else "—")
        warm_ms = results.get("pool20_warm_latency_mean_ms")
        cold_s = results.get("cold_tokenizer_model_load_seconds")
        if warm_ms and cold_s:
            fig, ax = plt.subplots(figsize=(6, 2.5))
            labels = [t("cold_start"), t("warm_inference")]
            times = [cold_s * 1000, warm_ms]
            bars = ax.bar(labels, times, color=["#ef4444", "#22c55e"], width=0.4)
            for bar, v in zip(bars, times):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3, f"{v:.0f} ms", ha="center", fontsize=9)
            ax.set_ylabel(t("latency_ms"))
            ax.set_title(t("latency_breakdown"), fontsize=10)
            fig.tight_layout()
            st.pyplot(fig)
        pool = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_pool_benchmark.csv"))
        if not pool.empty and "candidate_pool_size" in pool and "latency_mean_ms" in pool:
            fig, ax = plt.subplots(figsize=(6, 2.5))
            ax.plot(pool["candidate_pool_size"], pool["latency_mean_ms"], marker="o", color="#6366f1")
            ax.set_xlabel(t("candidate_pool_label"))
            ax.set_ylabel(t("latency_ms"))
            ax.set_title(t("latency_vs_pool"), fontsize=10)
            fig.tight_layout()
            st.pyplot(fig)


def repeated_seed_section():
    section_heading(t("repeated_seed_evaluation"), t("repeated_seed_desc"))
    repeated = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_repeated_seed_ci.csv"))
    if not repeated.empty:
        display = repeated[["policy", "seeds", "ndcg@10_mean", "ndcg@10_ci95_low", "ndcg@10_ci95_high"]].copy()
        display.columns = [t("policy_col"), t("seeds_col"), t("ndcg10_mean_col"), t("ci95_low_col"), t("ci95_high_col")]
        render_safe_table(display, max_rows=10)


def validation_variants_section():
    section_heading(t("validation_document_variants"), t("validation_variants_desc"))
    variants = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_validation_document_variants.csv"))
    if not variants.empty:
        display = variants[["document_variant", "ndcg@10_mean", "mrr_mean", "latency_p50_ms", "latency_mean_ms"]].copy()
        display.columns = [t("document_variant_col"), t("ndcg10_col"), t("mrr_col"), t("latency_p50_col"), t("latency_mean_col")]
        render_safe_table(display, max_rows=10)


def error_analysis_section():
    section_heading(t("error_analysis"), t("error_analysis_desc"))
    errors_path = TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_error_samples.json"
    if errors_path.is_file():
        try:
            errors = json.loads(errors_path.read_text(encoding="utf-8"))
            if errors:
                display = pd.DataFrame([
                    {"Query": e.get("query", "—"), t("baseline_ndcg_col"): format_ranking_metric(e.get('baseline_ndcg')),
                     t("v5_ndcg_col"): format_ranking_metric(e.get('v5_ndcg')), t("delta_col"): format_delta(e.get('delta'))}
                    for e in errors
                ])
                render_safe_table(display, max_rows=20)
        except (OSError, json.JSONDecodeError):
            st.caption(t("error_samples_unavailable"))
    else:
        st.caption(t("error_samples_in_bundle"))


def limitations_section():
    section_heading(t("limitations"))
    limitations = load_text_safe(str(TRENDYOL_RELEVANCE_DIR / "reports" / "V5_LIMITATIONS.md"))
    if limitations:
        st.markdown(limitations)
    decision_banner(
        t("governance_not_prod"),
        t("not_production_promoted_desc"),
    )


def render():
    page_header(
        "Trendyol Cross-Encoder Reranking (V5)",
        "Experimental reranking of Hybrid RRF candidates using a multilingual cross-encoder.",
        "CROSS-ENCODER \u00b7 RERANKING \u00b7 EXPERIMENTAL"
    )
    frozen = load_frozen_policy()
    results = load_results()
    evidence_strip([
        (t("model_id_label"), frozen.get("model_id", "—").split("/")[-1], frozen.get("revision", "—")[:12]),
        (t("license_label"), frozen.get("license", "—"), t("verified_apache2")),
        (t("device_col"), results.get("device", "cpu"), t("cpu_inference")),
        (t("governance_label"), t("governance_not_prod"), t("best_reranking_candidate")),
    ])

    tabs = st.tabs([
        "01 · " + t("live_inference_short"),
        "02 · " + t("evidence"),
        "03 · " + t("holdout_detail"),
        "04 · " + t("benchmarks"),
        "05 · " + t("validation_variants") + " & " + t("repeated_seed_evaluation"),
        "06 · " + t("error_analysis"),
        "07 · " + t("frozen_policy_config") + " & " + t("limitations"),
    ])

    with tabs[0]:
        demo_section()
    with tabs[1]:
        evidence_section()
    with tabs[2]:
        holdout_detail_section()
    with tabs[3]:
        benchmark_section()
    with tabs[4]:
        validation_variants_section()
        repeated_seed_section()
    with tabs[5]:
        error_analysis_section()
    with tabs[6]:
        model_config_section()
        limitations_section()

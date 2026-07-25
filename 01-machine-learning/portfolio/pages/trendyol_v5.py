"""V5 cross-encoder reranker UI page for the Trendyol search pipeline."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR, REPOSITORY_ROOT
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
    section_heading("Live Inference", "Cross-encoder reranking on a bounded 5,000-product preview catalogue.")
    st.warning("Cold model load may take several seconds on first inference. Model/tokenizer are cached after loading.")
    frozen = load_frozen_policy()
    left, right = st.columns(2)
    with left:
        st.metric("Policy", frozen.get("policy", "cross_encoder"))
        st.metric("Alpha", f"{frozen.get('alpha', 1.0):.2f}")
        st.metric("Document variant", frozen.get("document_variant", "title_compact_metadata"))
    with right:
        st.metric("Candidate pool", str(frozen.get("candidate_pool", 20)))
        st.metric("Batch size", str(frozen.get("batch_size", 8)))
        st.metric("Model", frozen.get("model_id", "—").split("/")[-1])

    preset = st.selectbox(t("nav_search_demo"), PRESETS, key="v5_demo_preset")
    query = st.text_input("Query", preset, key="v5_demo_query")
    if st.button(t("nav_cross_encoder"), key="v5_demo_run"):
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
                    "Sıra": r.get("final_rank", r.get("cross_encoder_rank", "—")),
                    "Ürün": r.get("title", "—"),
                    "Cross-encoder score": format_ranking_metric(r.get("cross_encoder_score")),
                    "Rank değişimi": r.get("rank_delta", "—"),
                    "Önceki sıra": r.get("pre_rerank_rank", "—"),
                })
            if display:
                render_safe_table(pd.DataFrame(display), max_rows=20)
            ce_meta = response.get("cross_encoder_metadata", {})
            if ce_meta:
                st.caption(
                    f"Model: {ce_meta.get('model_name', '—')} · "
                    f"Revision: {ce_meta.get('model_revision', '—')[:12]} · "
                    f"Variant: {ce_meta.get('document_variant', '—')} · "
                    f"Batch: {ce_meta.get('batch_size', '—')}"
                )
        else:
            st.error("Pipeline unavailable.")

    counters = v5_load_counters()
    st.caption(
        f"Model load count: {counters.get('model_load_count', '—')} · "
        f"Tokenizer load count: {counters.get('tokenizer_load_count', '—')} · "
        f"Model loaded: {'Yes' if counters.get('model_loaded') else 'No'}"
    )


def evidence_section():
    section_heading("Offline Evaluation", "Holdout results on 150 frozen queries (seed 42, pool 20).")
    results = load_results()
    if not results:
        st.warning("V5 results are not available.")
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
        ("Hybrid RRF NDCG@10", format_ranking_metric(baseline_ndcg), "V5 holdout baseline"),
        ("V5 NDCG@10", format_ranking_metric(v5_ndcg), "Cross-encoder reranking"),
        ("Absolute Δ", format_delta(delta), f"Relative: +{rel_pct:.1f}%" if isinstance(rel_pct, float) else ""),
        ("MRR Δ", format_delta(mrr_delta), "Paired bootstrap"),
    ])

    decision_banner(
        "Best Reranking Research Candidate · Not Production Promoted",
        "The cross-encoder reranker improved NDCG@10 on the frozen 150-query V5 holdout. "
        "It is an experimental reranker on a bounded demo; no production SLA or business impact is claimed."
    )

    cols = st.columns(2)
    with cols[0]:
        st.metric("Improved queries", str(improved))
        st.metric("Unchanged queries", str(unchanged))
        if ndcg_ci:
            st.info(f"NDCG@10 95% CI: [{format_ranking_metric(ndcg_ci[0])}, {format_ranking_metric(ndcg_ci[1])}]")
    with cols[1]:
        st.metric("Worsened queries", str(worsened))
        st.metric("Total queries", str(results.get("holdout_query_count", "—")))
        if mrr_ci:
            st.caption(f"MRR 95% CI: [{format_ranking_metric(mrr_ci[0])}, {format_ranking_metric(mrr_ci[1])}]")


def holdout_detail_section():
    section_heading("Holdout Detail", "Per-policy aggregate metrics on the frozen holdout.")
    holdout = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_holdout_summary.csv"))
    if not holdout.empty:
        display = holdout[["policy", "ndcg@10_mean", "mrr_mean", "candidate_recall@20_mean"]].copy()
        display.columns = ["Policy", "NDCG@10", "MRR", "Candidate Recall@20"]
        render_safe_table(display, max_rows=10)
    section_heading("Paired Bootstrap Results", "Query-level paired comparison vs Hybrid RRF baseline.")
    paired = load_paired()
    if not paired.empty:
        display = paired[paired.metric.isin(["ndcg@10", "mrr"])][["candidate", "metric", "delta", "ci_low", "ci_high", "improved", "unchanged", "worsened"]].copy()
        render_safe_table(display, max_rows=10)


def segment_section():
    section_heading("Query Segment Analysis", "Per-segment V5 impact on NDCG@10 and MRR.")
    segment_path = TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_query_segment_metrics.csv"
    segment = load_csv_safe(str(segment_path)) if segment_path.is_file() else pd.DataFrame()
    if not segment.empty:
        render_safe_table(segment, max_rows=20)
    else:
        st.caption("Segment analysis outputs are available in the offline evaluation bundle.")


def model_config_section():
    section_heading("Frozen Policy Configuration", "Selected by validation-only evaluation.")
    frozen = load_frozen_policy()
    rows = [{"Parameter": k, "Value": v} for k, v in frozen.items() if k != "governance"]
    render_safe_table(pd.DataFrame(rows), max_rows=20)
    decision_banner("Governance", frozen.get("governance", "Best Reranking Research Candidate · Not Production Promoted"))


def benchmark_section():
    section_heading("Batch Benchmark", "Pool 20, title_compact_metadata, 30 validation queries, CPU.")
    batch = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_batch_benchmark.csv"))
    if not batch.empty:
        render_safe_table(batch, max_rows=10)
    section_heading("Pool Benchmark", "Selected variant, batch 8, validation queries, CPU.")
    pool = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_pool_benchmark.csv"))
    if not pool.empty:
        render_safe_table(pool, max_rows=10)
    section_heading("Warm Latency", "Holdout latency (150 queries, pool 20).")
    results = load_results()
    if results:
        st.metric("Mean warm latency (ms)", f"{results.get('pool20_warm_latency_mean_ms', 0):.1f}" if isinstance(results.get('pool20_warm_latency_mean_ms'), (int, float)) else "—")
        st.metric("P50 warm latency (ms)", f"{results.get('pool20_warm_latency_p50_ms', 0):.1f}" if isinstance(results.get('pool20_warm_latency_p50_ms'), (int, float)) else "—")
        st.metric("P95 warm latency (ms)", f"{results.get('pool20_warm_latency_p95_ms', 0):.1f}" if isinstance(results.get('pool20_warm_latency_p95_ms'), (int, float)) else "—")
        st.metric("Cold load (s)", f"{results.get('cold_tokenizer_model_load_seconds', 0):.2f}" if isinstance(results.get('cold_tokenizer_model_load_seconds'), (int, float)) else "—")


def repeated_seed_section():
    section_heading("Repeated-Seed Evaluation", "Five group-safe seeds (42, 52, 62, 72, 82).")
    repeated = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_repeated_seed_ci.csv"))
    if not repeated.empty:
        display = repeated[["policy", "seeds", "ndcg@10_mean", "ndcg@10_ci95_low", "ndcg@10_ci95_high"]].copy()
        display.columns = ["Policy", "Seeds", "NDCG@10 Mean", "CI Low", "CI High"]
        render_safe_table(display, max_rows=10)


def validation_variants_section():
    section_heading("Validation Document Variants", "Candidate document templates compared on 150 validation queries (pool 20, pure CE).")
    variants = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_validation_document_variants.csv"))
    if not variants.empty:
        display = variants[["document_variant", "ndcg@10_mean", "mrr_mean", "latency_p50_ms", "latency_mean_ms"]].copy()
        display.columns = ["Document Variant", "NDCG@10", "MRR", "Latency P50 (ms)", "Latency Mean (ms)"]
        render_safe_table(display, max_rows=10)


def error_analysis_section():
    section_heading("Error Analysis", "Bounded error examples from holdout (no raw catalogue data).")
    errors_path = TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_error_samples.json"
    if errors_path.is_file():
        try:
            errors = json.loads(errors_path.read_text(encoding="utf-8"))
            if errors:
                display = pd.DataFrame([
                    {"Query": e.get("query", "—"), "Baseline NDCG": format_ranking_metric(e.get('baseline_ndcg')),
                     "V5 NDCG": format_ranking_metric(e.get('v5_ndcg')), "Δ": format_delta(e.get('delta'))}
                    for e in errors
                ])
                render_safe_table(display, max_rows=20)
        except (OSError, json.JSONDecodeError):
            st.caption("Error samples unavailable.")
    else:
        st.caption("Error samples are available in the offline evaluation bundle.")


def limitations_section():
    section_heading("Limitations")
    limitations = load_text_safe(str(TRENDYOL_RELEVANCE_DIR / "reports" / "V5_LIMITATIONS.md"))
    if limitations:
        st.markdown(limitations)
    decision_banner(
        "Governance",
        "Best Reranking Research Candidate · Not Production Promoted. "
        "The cross-encoder is an experimental reranker on a bounded 5,000-product demo. "
        "No production SLA, online A/B test, or business impact is claimed."
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
        ("Model", frozen.get("model_id", "—").split("/")[-1], frozen.get("revision", "—")[:12]),
        ("License", frozen.get("license", "—"), "Verified Apache-2.0"),
        ("Device", results.get("device", "cpu"), "CPU inference"),
        ("Governance", "Not Production Promoted", "Best Reranking Research Candidate"),
    ])

    tabs = st.tabs([
        "01 · Live Demo",
        "02 · Evidence",
        "03 · Holdout Detail",
        "04 · Benchmarks",
        "05 · Validation & Seeds",
        "06 · Error Analysis",
        "07 · Configuration & Limitations",
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

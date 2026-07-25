from __future__ import annotations

import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe
from portfolio.project_registry import get_project_registry
from portfolio.ui_components import (comparison_cards, decision_banner,
                                     hero_panel, kpi_grid_mixed,
                                     model_stage_timeline, render_safe_table,
                                     section_heading, status_badge)


def render() -> None:
    hero_panel(
        title="Trendyol Search Intelligence",
        subtitle=t("subtitle_trendyol_relevance"),
        kicker=t("section_search"),
    )

    projects = {p["id"]: p for p in get_project_registry()}
    metrics = load_json_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "metrics.json"))

    section_heading("Executive Summary")
    kpi_grid_mixed([
        ("V1 Champion", f"F1 {metrics.get('f1', 0):.4f}", status_badge("verified")),
        ("V3 Hybrid RRF", f"Recall@50 0.8314", status_badge("experimental")),
        ("V4 Pipeline", f"NDCG@10 0.6191", status_badge("experimental")),
        ("V5 Reranker", "NDCG@10 0.6785", status_badge("experimental")),
        ("Governance", "Not Production Promoted", "Best Reranking Research Candidate"),
    ])

    section_heading("Version Evolution")
    model_stage_timeline([
        ("V0", "Dummy baseline", "Minimum reference", "available"),
        ("V1", "Sparse-text classifier", "Word/character TF-IDF + Logistic Regression", "verified"),
        ("V2", "Classical challengers", "Trees, calibration, hard negatives", "experimental"),
        ("V2 Ranking", "Learning to rank", "XGBoost + query bootstrap", "experimental"),
        ("V2.1", "Robust evaluation", "1,000 groups × five seeds", "experimental"),
        ("V3", "Candidate retrieval", "TF-IDF/BM25 + E5 semantic", "experimental"),
        ("V4", "End-to-end pipeline", "Hybrid RRF + governance", "experimental"),
        ("V5", "Cross-encoder reranking", "mmarco-mMiniLMv2 · NDCG +0.0664", "experimental"),
    ])

    section_heading("V1 — Verified Champion")
    v1 = projects.get("trendyol_relevance", {})
    comparison_cards([{
        "title": "V1 Verified Champion",
        "status": "verified",
        "kind": "champion",
        "algorithm": "TF-IDF + similarity + Logistic Regression",
        "metric": f"F1 {metrics.get('f1', 0):.4f} · PR AUC {metrics.get('pr_auc', 0):.4f}",
        "note": "Stable live probability inference.",
    }])

    section_heading("V2–V2.1 — Historical Research (Not Promoted)")
    comparison_cards([
        {
            "title": "V2 Classification Challenger",
            "status": "experimental",
            "kind": "experimental",
            "algorithm": "Random Forest",
            "metric": f"Holdout F1 {projects.get('trendyol_v2_classifier', {}).get('primary_metric_value', '—')}",
            "note": "Not Promoted.",
        },
        {
            "title": "V2.1 Best Research Candidate",
            "status": "experimental",
            "kind": "experimental",
            "algorithm": "HistGradientBoosting",
            "metric": f"Mean F1 {projects.get('trendyol_v21_classifier', {}).get('primary_metric_value', '—')}",
            "note": "Offline Evaluation; Different historical split.",
        },
    ])

    section_heading("V3/V3.1 — Retrieval Research")
    v3_hybrid = projects.get("trendyol_v31_hybrid", {})
    comparison_cards([{
        "title": "V3.1 Best Research Candidate",
        "status": "experimental",
        "kind": "experimental",
        "algorithm": "Hybrid RRF",
        "metric": f"Recall@50 {v3_hybrid.get('primary_metric_value', '—')}",
        "note": "Bounded Preview · Offline Evaluation · Not Promoted",
    }])

    section_heading("V4 — End-to-End Pipeline")
    v4 = projects.get("trendyol_v4_pipeline", {})
    comparison_cards([{
        "title": "V4 Pipeline",
        "status": "experimental",
        "kind": "experimental",
        "algorithm": "Hybrid RRF retrieval-only",
        "metric": f"Recall@50 {v4.get('primary_metric_value', '—')} · NDCG@10 {v4.get('secondary_metrics', {}).get('NDCG@10', '—')}",
        "note": "Not Production Promoted",
    }])

    section_heading("V5 — Cross-Encoder Reranking")
    v5 = projects.get("trendyol_v5_reranker", {})
    sec = v5.get("secondary_metrics", {})
    st.markdown(
        f"""
<div class="kpi-grid">
<div class="metric-card"><small>Hybrid RRF NDCG@10</small><strong>{sec.get('holdout_hybrid_rrf_ndcg@10', '—')}</strong></div>
<div class="metric-card"><small>Cross-Encoder NDCG@10</small><strong>{v5.get('primary_metric_value', '—')}</strong></div>
<div class="metric-card"><small>Absolute Gain</small><strong>+{sec.get('absolute_ndcg_delta', '—')}</strong><span>+{sec.get('relative_ndcg_pct', '—')}%</span></div>
<div class="metric-card"><small>Confidence Interval</small><strong>{v5.get('paired_ndcg_ci95', ['—'])[0]:.4f} – {v5.get('paired_ndcg_ci95', ['—', '—'])[1]:.4f}</strong><span>95% paired bootstrap</span></div>
<div class="metric-card"><small>Improved / Worsened</small><strong>{v5.get('paired_improved', '—')} / {v5.get('paired_worsened', '—')}</strong><span>of 150 holdout queries</span></div>
<div class="metric-card"><small>Warm Latency (p95)</small><strong>{sec.get('warm_latency_p95_ms', '—')} ms</strong><span>pool 20 · CPU</span></div>
</div>
""",
        unsafe_allow_html=True,
    )
    decision_banner(
        "Best Reranking Research Candidate · Not Production Promoted",
        "Pure cross-encoder policy (alpha=1.0) on title_compact_metadata. "
        "Candidate pool 20, batch size 8. "
        "Model: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 revision 1427fd65.",
    )

    section_heading("Research Roadmap")
    st.markdown(
        """
<div class="card-grid" style="grid-template-columns:repeat(auto-fit,minmax(180px,1fr))">
<div class="card"><h3>V2.1</h3>""" + status_badge("available") + """<p>Robust Evaluation</p></div>
<div class="card"><h3>V3.1</h3>""" + status_badge("available") + """<p>Semantic Retrieval</p></div>
<div class="card"><h3>V4</h3>""" + status_badge("available") + """<p>Pipeline</p></div>
<div class="card"><h3>V5</h3>""" + status_badge("available") + """<p>Cross-Encoder</p></div>
<div class="card"><h3>Online Evaluation</h3>""" + status_badge("roadmap") + """<p>Next: A/B testing</p></div>
<div class="card"><h3>Scalable Serving</h3>""" + status_badge("roadmap") + """<p>Future</p></div>
</div>
""",
        unsafe_allow_html=True,
    )

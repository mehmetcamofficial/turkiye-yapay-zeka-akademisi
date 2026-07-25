from __future__ import annotations

import streamlit as st

from portfolio.i18n import t
from portfolio.loaders import load_json_safe
from portfolio.project_registry import get_project_registry, portfolio_counts
from portfolio.ui_components import (evidence_strip, hero_panel, kpi_grid,
                                     section_heading, status_badge)

TRENDYOL_RELEVANCE_DIR = __import__(
    "portfolio.config", fromlist=["TRENDYOL_RELEVANCE_DIR"]
).TRENDYOL_RELEVANCE_DIR


def render() -> None:
    hero_panel(
        title="AI & Search Intelligence Engineering Portfolio",
        subtitle=t(
            "nav_executive_overview",
        ) + " — " + (
            "Arama, sıralama ve makine öğrenmesi sistemlerini "
            "doğrulanabilir deneylerden çalışan portföy ürünlerine dönüştürüyorum."
        ),
    )

    counts = portfolio_counts()
    kpi_grid([
        (t("sidebar_completed"), str(counts["completed_projects"]),
         t("sidebar_pipelines") + f': {counts["completed_pipelines"]}'),
        (t("sidebar_models"), str(counts["models_compared"]), "Across all projects"),
        ("V5 NDCG@10", "0.6785", "Cross-Encoder Reranking"),
        ("NDCG@10 Gain", "+0.0664 (+10.8%)", "vs Hybrid RRF baseline"),
        ("Tests", "51 passing", "Trendyol Search suite"),
        ("Query Leakage", "0", "Group-safe term_id splits"),
    ])

    section_heading(
        "Featured Project: Search Intelligence",
        "V1–V5 research pipeline: classification, retrieval, ranking, reranking",
    )

    projects = get_project_registry()
    by_id = {p["id"]: p for p in projects}

    v5 = by_id.get("trendyol_v5_reranker", {})
    v4 = by_id.get("trendyol_v4_pipeline", {})
    v1 = by_id.get("trendyol_relevance", {})

    evidence_strip([
        ("V1 Champion", f"F1 {v1.get('primary_metric_value', '—')}", status_badge(v1.get("status", "experimental"))),
        ("V4 Pipeline", f"Recall@50 {v4.get('primary_metric_value', '—')}", status_badge(v4.get("status", "experimental"))),
        ("V5 Reranker", f"NDCG@10 {v5.get('primary_metric_value', '—')}", status_badge(v5.get("status", "experimental"))),
        ("NDCG Gain", f"+{v5.get('secondary_metrics', {}).get('absolute_ndcg_delta', '—')}", "Holdout CI [0.0368, 0.0960]"),
        ("Governance", "Not Production Promoted", "Best Reranking Research Candidate"),
    ])

    section_heading(
        "What to explore first",
        t("nav_search_demo") + " · " + t("nav_cross_encoder") + " · Model Registry · Artifact Health",
    )

    section_heading("Research Roadmap", "Completed and upcoming work")
    st.markdown(
        """
<div class="card-grid" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr))">
<div class="card"><h3>V2.1 Robust Evaluation</h3>"""
        + status_badge("available") + """<p>Completed research</p></div>
<div class="card"><h3>V3.1 Semantic Retrieval</h3>"""
        + status_badge("available") + """<p>Completed research</p></div>
<div class="card"><h3>V4 Pipeline</h3>"""
        + status_badge("available") + """<p>Completed research</p></div>
<div class="card"><h3>V5 Cross-Encoder</h3>"""
        + status_badge("available") + """<p>Completed research</p></div>
<div class="card"><h3>Online Evaluation Framework</h3>"""
        + status_badge("roadmap") + """<p>Next: online A/B testing framework</p></div>
<div class="card"><h3>Observability & Monitoring</h3>"""
        + status_badge("roadmap") + """<p>Next: production observability</p></div>
<div class="card"><h3>Scalable Serving</h3>"""
        + status_badge("roadmap") + """<p>Next: scalable inference</p></div>
</div>
""",
        unsafe_allow_html=True,
    )

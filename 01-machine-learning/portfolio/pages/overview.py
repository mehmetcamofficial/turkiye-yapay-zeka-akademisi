from __future__ import annotations

import streamlit as st

from portfolio.i18n import t
from portfolio.loaders import load_json_safe
from portfolio.project_registry import get_project_registry, portfolio_counts
from portfolio.ui_components import (card_grid, hero_panel, kpi_grid,
                                     kpi_grid_mixed, section_heading,
                                     status_badge, format_ranking_metric,
                                     format_delta)

TRENDYOL_RELEVANCE_DIR = __import__(
    "portfolio.config", fromlist=["TRENDYOL_RELEVANCE_DIR"]
).TRENDYOL_RELEVANCE_DIR


def render() -> None:
    hero_panel(
        title="AI & Search Intelligence Engineering Portfolio",
        subtitle=t("subtitle_overview"),
    )

    counts = portfolio_counts()
    kpi_grid([
        (t("sidebar_completed"), str(counts["completed_projects"]),
         f'{t("sidebar_pipelines")}: {counts["completed_pipelines"]}'),
        (t("sidebar_models"), str(counts["models_compared"]), "Across all projects"),
        ("V5 NDCG@10", "0.6785", "Cross-Encoder Reranking"),
        ("NDCG@10 Gain", "+0.0664 (+10.8%)", "vs Hybrid RRF baseline"),
    ])

    section_heading(
        "Featured Project: Search Intelligence",
        "V1\u2013V5 research pipeline: classification, retrieval, ranking, reranking",
    )

    projects = get_project_registry()
    by_id = {p["id"]: p for p in projects}
    v5 = by_id.get("trendyol_v5_reranker", {})
    v4 = by_id.get("trendyol_v4_pipeline", {})
    v1 = by_id.get("trendyol_relevance", {})

    kpi_grid_mixed([
        ("V1 Champion", status_badge(v1.get("status", "experimental")), None),
        ("V4 Pipeline", status_badge(v4.get("status", "experimental")), None),
        ("V5 Reranker", status_badge(v5.get("status", "experimental")), None),
        ("Governance", "Not Production Promoted", "Best Reranking Research Candidate"),
    ])

    section_heading("Research Roadmap")
    st.markdown(
        f"""
<div class="card-grid">
<div class="card"><h3>V2.1 Robust Evaluation</h3>{status_badge("available")}<p>Completed research</p></div>
<div class="card"><h3>V3.1 Semantic Retrieval</h3>{status_badge("available")}<p>Completed research</p></div>
<div class="card"><h3>V4 Pipeline</h3>{status_badge("available")}<p>Completed research</p></div>
<div class="card"><h3>V5 Cross-Encoder</h3>{status_badge("available")}<p>Completed research</p></div>
<div class="card"><h3>Online Evaluation</h3>{status_badge("roadmap")}<p>Next: A/B testing framework</p></div>
<div class="card"><h3>Scalable Serving</h3>{status_badge("roadmap")}<p>Future work</p></div>
</div>
""",
        unsafe_allow_html=True,
    )

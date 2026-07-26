from __future__ import annotations

import streamlit as st

import matplotlib.pyplot as plt

from portfolio.i18n import t
from portfolio.loaders import load_json_safe
from portfolio.project_registry import get_project_registry, portfolio_counts
from portfolio.ui_components import (card_grid, hero_panel, kpi_grid,
                                     kpi_grid_mixed, section_heading,
                                     status_badge, format_ranking_metric,
                                     format_delta)


def render() -> None:
    hero_panel(
        title=t("nav_overview"),
        subtitle=t("product_positioning_hero"),
    )

    counts = portfolio_counts()
    kpi_grid([
        (t("sidebar_completed"), str(counts["completed_projects"]),
         f'{t("sidebar_pipelines")}: {counts["completed_pipelines"]}'),
        (t("sidebar_models"), str(counts["models_compared"]), "Across all products"),
    ])

    section_heading(
        t("product_mission"),
        t("product_mission_desc"),
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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.5))
    categories = {}
    for p in projects:
        cat = p.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1
    cats, vals = zip(*sorted(categories.items(), key=lambda x: -x[1]))
    ax1.barh(cats, vals, color="#4f46e5", height=0.6)
    ax1.set_xlabel(t("project_count"))
    ax1.set_title(t("project_distribution"), fontsize=10)
    statuses = {"available": 0, "experimental": 0, "roadmap": 0, "verified": 0}
    for p in projects:
        s = p.get("status", "roadmap")
        statuses[s] = statuses.get(s, 0) + 1
    labels, svals = zip(*statuses.items())
    colors = ["#22c55e", "#eab308", "#ef4444", "#3b82f6"]
    ax2.bar(labels, svals, color=colors, width=0.5)
    ax2.set_title(t("status_distribution"), fontsize=10)
    ax2.tick_params(axis="x", rotation=45)
    for i, v in enumerate(svals):
        ax2.text(i, v + 0.1, str(v), ha="center", fontsize=9)
    fig.tight_layout()
    st.pyplot(fig)

    section_heading(t("enterprise_snapshot"))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**{t('status_operational')}**  \n{t('capability_real_data')}")
        st.markdown(f"**{t('status_operational')}**  \n{t('capability_trained_models')}")
        st.markdown(f"**{t('status_operational')}**  \n{t('capability_live_inference')}")
        st.markdown(f"**{t('status_operational')}**  \n{t('capability_hybrid_search')}")
        st.markdown(f"**{t('status_operational')}**  \n{t('capability_cross_encoder')}")
        st.markdown(f"**{t('status_operational')}**  \n{t('capability_model_registry')}")
    with col2:
        st.markdown(f"**{t('status_operational')}**  \n{t('capability_artifact_health')}")
        st.markdown(f"**{t('status_operational')}**  \n{t('capability_cloud_deployment')}")
        st.markdown(f"**{t('status_validated')}**  \n{t('capability_production_api')}")
        st.markdown(f"**{t('status_roadmap')}**  \n{t('capability_auth_sso')}")
        st.markdown(f"**{t('status_roadmap')}**  \n{t('capability_observability')}")
        st.markdown(f"**{t('status_roadmap')}**  \n{t('capability_horizontal_scaling')}")
    with col3:
        st.markdown(f"**{t('status_roadmap')}**  \n{t('capability_online_ab')}")

    st.divider()

    section_heading(t("search_intelligence_title"), t("search_intelligence_desc"))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{t('nav_relevance_classification')}**  \nV1 TF-IDF + Logistic Regression · F1 0.6260")
        st.markdown(f"**{t('nav_hybrid_retrieval')}**  \nV4 Hybrid RRF k=20 · NDCG@10 0.6191")
        st.markdown(f"**{t('nav_cross_encoder')}**  \nV5 mmarco-mMiniLMv2 · NDCG@10 0.6785 (+10.8%)")
    with col2:
        st.markdown(f"**{t('nav_policy_comparison')}**  \nBaseline vs reranked · paired bootstrap CI")
        st.markdown(f"**{t('nav_live_inference')}**  \n5,000-product demo · cold ~3–5s · warm p95 ~200ms")
        st.markdown(f"**{t('nav_runtime_diagnostics')}**  \nModel load count · tokenizer load · fallback state")

    st.divider()

    section_heading(t("ml_capabilities_title"), t("ml_capabilities_desc"))
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"### {t('nav_churn')}")
        st.caption("Logistic Regression · predict_proba · risk bands")
        st.caption(f"Test ROC AUC 0.844 · Recall 0.652")
    with c2:
        st.markdown(f"### {t('nav_housing')}")
        st.caption("Linear Regression · deterministic · $ output")
        st.caption(f"Test R² 0.80 · RMSE 0.47")
    with c3:
        st.markdown(f"### {t('nav_sentiment')}")
        st.caption("TF-IDF + Logistic Regression · binary")
        st.caption(f"Test F1 0.80 · Accuracy 0.81")

    st.divider()

    section_heading(t("data_intelligence_title"), t("data_intelligence_desc"))
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(f"**{t('nav_inventory')}**  \n7 Trendyol tables · 962K+ products")
    with d2:
        st.markdown(f"**{t('nav_quality')}**  \nSampled 20K/table · duplicates · nulls")
    with d3:
        st.markdown(f"**{t('nav_schema')}**  \n11 required fields · 7 supported questions")

    st.divider()

    section_heading(t("model_ops_title"), t("model_ops_desc"))
    o1, o2, o3 = st.columns(3)
    with o1:
        st.markdown(f"**{t('nav_registry')}**  \nActive models · version · decision · metric")
    with o2:
        st.markdown(f"**{t('nav_artifact_health')}**  \nCore · optional · local · cloud-excluded")
    with o3:
        st.markdown(f"**{t('nav_deployment')}**  \nCloud-ready · pinned deps · lazy load")

    st.divider()

    section_heading(t("enterprise_readiness_title"), t("enterprise_readiness_desc"))
    e1, e2, e3 = st.columns(3)
    with e1:
        st.markdown(f"**{t('capability_production_api')}**  \n{t('status_roadmap')}")
    with e2:
        st.markdown(f"**{t('capability_auth_sso')}**  \n{t('status_roadmap')}")
    with e3:
        st.markdown(f"**{t('capability_observability')}**  \n{t('status_roadmap')}")

    st.divider()

    section_heading(t("validated_results_title"), t("validated_results_desc"))
    st.markdown(f"**V1 F1:** 0.6260  ·  **V4 NDCG@10:** 0.6191  ·  **V5 NDCG@10:** 0.6785  ·  **Gain:** +10.8%  ·  **95% CI:** [0.0368, 0.0960]")

    st.divider()

    section_heading(t("architecture_title"), t("architecture_desc"))
    st.markdown("Two-stage retrieval → Hybrid RRF k=20 → Cross-encoder rerank (α=1.0) · Deterministic tie-breaking by item_id · Explicit retrieval-only fallback on reranker failure · Revision-pinned HuggingFace models")

    st.divider()

    section_heading(t("explore_first"), "")
    st.markdown(f"1. **{t('explore_search')}** — Interactive V5 cross-encoder reranking on 5K products")
    st.markdown(f"2. **{t('explore_data')}** — Schema health, category/brand structure, text quality")
    st.markdown(f"3. **{t('explore_ml')}** — Churn probability + risk band for single customer")
    st.markdown(f"4. **{t('explore_registry')}** — Active models, governance decisions, artifact paths")

    st.divider()

    section_heading(t("current_limitations"))
    st.markdown(f"• {t('limitation_no_production')}")
    st.markdown(f"• {t('limitation_cloud_excluded')}")
    st.markdown(f"• {t('limitation_bounded')}")
    st.markdown(f"• {t('limitation_no_auth')}")
    st.markdown(f"• {t('limitation_no_scaling')}")

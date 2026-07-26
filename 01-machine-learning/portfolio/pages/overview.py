from __future__ import annotations

import streamlit as st

from portfolio.i18n import t
from portfolio.ui_components import hero_panel, section_heading, status_badge

NAV_TARGETS: dict[str, tuple[str, str]] = {
    "search_demo": ("nav_search_intelligence", "section_search"),
    "live_inference": ("nav_live_inference", "section_search"),
    "churn": ("nav_churn", "section_ml"),
    "regression": ("nav_housing", "section_ml"),
    "nlp": ("nav_sentiment", "section_ml"),
    "data_science_overview": ("nav_data_workspace", "section_data_science"),
    "model_registry": ("nav_registry", "section_model_ops"),
}


def _navigate_to(page_key: str) -> None:
    nav_key, section = NAV_TARGETS[page_key]
    st.session_state["nav_section"] = section
    st.session_state[f"nav_page_{section}"] = nav_key


def render() -> None:
    hero_panel(
        title=t("nav_overview"),
        subtitle=t("product_positioning_hero"),
    )

    # ---- System Status ----
    section_heading(t("system_status"), t("system_status_desc"))
    sys_items = [
        (t("capability_real_data"), "available"),
        (t("capability_trained_models"), "available"),
        (t("capability_live_inference"), "available"),
        (t("capability_hybrid_search"), "available"),
        (t("capability_cross_encoder"), "available"),
        (t("capability_model_registry"), "available"),
    ]
    sys_cols = st.columns(6)
    for col, (label, status) in zip(sys_cols, sys_items):
        with col:
            st.markdown(
                f"<div style='text-align:center'><strong>{label}</strong>"
                f"<br>{status_badge(status)}</div>",
                unsafe_allow_html=True,
            )

    # ---- Latest Validated Metrics ----
    section_heading(t("validated_results_title"), "")
    metric_data = [
        (t("metric_v1_f1"), "0.6260", None),
        (t("metric_v4_ndcg10"), "0.6191", None),
        (t("metric_v5_ndcg10"), "0.6785", "+10.8%"),
        (t("metric_ci95"), "[0.0368, 0.0960]", None),
        (t("metric_mrr"), "0.7720", None),
    ]
    m_cols = st.columns(5)
    for col, (label, value_str, delta) in zip(m_cols, metric_data):
        with col:
            st.metric(label, value_str, delta=delta)

    # ---- V1–V5 Evolution ----
    section_heading(t("v1_v5_evolution"), t("v1_v5_evolution_desc"))
    v_cols = st.columns(5)
    versions = [
        ("V1", "TF-IDF + Logistic Regression", "F1 0.6260", "verified"),
        ("V2", "RF / XGBRanker Challenger", "Offline eval", "experimental"),
        ("V3", "Semantic Retrieval", "Recall@50 0.83+", "experimental"),
        ("V4", "Hybrid RRF Pipeline", "NDCG@10 0.6191", "experimental"),
        ("V5", "Cross-Encoder Reranking", "NDCG@10 0.6785", "experimental"),
    ]
    for col, (ver, algo, metric, badge) in zip(v_cols, versions):
        with col:
            st.markdown(
                f'<div class="card" style="text-align:center">'
                f"{status_badge(badge)}"
                f"<h3>{ver}</h3>"
                f"<p>{algo}<br><strong>{metric}</strong></p></div>",
                unsafe_allow_html=True,
            )

    # ---- Search Pipeline Architecture ----
    st.divider()
    section_heading(t("architecture_title"), t("architecture_desc"))
    st.info(
        "Two-stage retrieval → Hybrid RRF k=20 → "
        "Cross-encoder rerank (α=1.0) · "
        "Deterministic tie-breaking by item_id · "
        "Explicit retrieval-only fallback on reranker failure · "
        "Revision-pinned HuggingFace models"
    )

    # ---- Runtime Readiness ----
    section_heading(t("runtime_readiness"), t("runtime_readiness_desc"))
    r_cols = st.columns(3)
    runtime_cards = [
        (t("runtime_cold_start"), "~2s model load · cached after first inference"),
        (t("runtime_warm_latency"), "~200ms at pool=20"),
        (t("runtime_fallback"), "Retrieval-only on reranker failure"),
    ]
    for col, (title, desc) in zip(r_cols, runtime_cards):
        with col:
            st.markdown(
                f"<div class='card'><h3>{title}</h3>"
                f"<p>{desc}<br>"
                f"{status_badge('available')}</p></div>",
                unsafe_allow_html=True,
            )

    # ---- Dataset Footprint ----
    section_heading(t("dataset_footprint"), t("dataset_footprint_desc"))
    d_cols = st.columns(4)
    d_items = [
        (t("footprint_tables"), "7", "Trendyol e-commerce"),
        (t("footprint_products"), "962K+", "Catalogue-wide"),
        (t("footprint_queries"), "1,000", "Evaluation set"),
        (t("footprint_demo"), "5,000", "Bounded catalogue"),
    ]
    for col, (label, value, note) in zip(d_cols, d_items):
        with col:
            st.markdown(
                f"<div class='metric-card'><small>{label}</small>"
                f"<strong>{value}</strong><span>{note}</span></div>",
                unsafe_allow_html=True,
            )

    # ---- Capability Maturity ----
    section_heading(t("capability_maturity"), t("capability_maturity_desc"))
    caps = [
        ("Real Dataset", "available"),
        ("Trained Models", "available"),
        ("Live Inference", "available"),
        ("Hybrid Search", "available"),
        ("Cross-Encoder", "available"),
        ("Model Registry", "available"),
        ("Artifact Health", "available"),
        ("Cloud Deployment", "available"),
        ("Production API", "roadmap"),
        ("Auth / SSO", "roadmap"),
        ("Observability", "roadmap"),
        ("Horizontal Scaling", "roadmap"),
    ]
    cap_cols = st.columns(4)
    for i, (cap, cap_status) in enumerate(caps):
        with cap_cols[i % 4]:
            st.markdown(
                f"<strong>{cap}</strong><br>{status_badge(cap_status)}",
                unsafe_allow_html=True,
            )

    # ---- Project Cards with CTAs ----
    st.divider()
    section_heading(t("product_modules"), t("product_modules_desc"))

    cta_sections = [
        [
            ("search_demo", t("nav_search_intelligence"),
             "Interactive V5 cross-encoder reranking on 5K products"),
            ("live_inference", t("nav_live_inference"),
             "5,000-product demo · cold ~3-5s · warm p95 ~200ms"),
        ],
        [
            ("churn", t("nav_churn"),
             "Logistic Regression · ROC AUC 0.844 · Recall 0.652"),
            ("regression", t("nav_housing"),
             "Linear Regression · R² 0.80 · RMSE 0.47"),
            ("nlp", t("nav_sentiment"),
             "TF-IDF + LR · F1 0.80 · Accuracy 0.81"),
        ],
        [
            ("data_science_overview", t("nav_data_workspace"),
             "7 Trendyol tables · 962K+ products · Schema & quality"),
            ("model_registry", t("nav_registry"),
             "Active models · governance · artifact health"),
        ],
    ]

    cta_keys = {
        "search_demo": "cta_search_intelligence",
        "live_inference": "cta_live_inference",
        "churn": "cta_churn",
        "regression": "cta_housing",
        "nlp": "cta_sentiment",
        "data_science_overview": "cta_data_intelligence",
        "model_registry": "cta_model_ops",
    }

    for row in cta_sections:
        cols = st.columns(len(row))
        for col, (page_key, title_text, desc_text) in zip(cols, row):
            with col:
                st.markdown(
                    f'<div class="card"><h3>{title_text}</h3>'
                    f"<p>{desc_text}</p></div>",
                    unsafe_allow_html=True,
                )
                st.button(
                    t(cta_keys[page_key]),
                    on_click=_navigate_to,
                    args=(page_key,),
                    use_container_width=True,
                )

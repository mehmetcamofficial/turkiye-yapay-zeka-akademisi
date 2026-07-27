from __future__ import annotations

import streamlit as st

from portfolio.config import DATA_SCIENCE_FINAL_DIR, TRENDYOL_RELEVANCE_DIR
from portfolio.data_science_registry import evaluate_final_project
from portfolio.i18n import t
from portfolio.loaders import load_json_safe, load_text_safe
from portfolio.ui_components import (evidence_strip, hero_panel, information_panel,
                                     kpi_grid, render_safe_table, section_heading,
                                     status_badge)


def render() -> None:
    item = evaluate_final_project()
    hero_panel(
        title=t("search_intelligence_research_title"),
        subtitle=t("search_intelligence_research_subtitle"),
        kicker=t("section_search"),
    )
    st.markdown(status_badge(item["status"]), unsafe_allow_html=True)

    v5_results = load_json_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_results.json"))
    v1_metrics = load_json_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "metrics.json"))

    tabs = st.tabs([
        t("tab_product_overview"),
        t("tab_data_foundation"),
        t("tab_system_evolution"),
        t("tab_retrieval_arch"),
        t("tab_ranking_reranking"),
        t("tab_evaluation"),
        t("tab_live_inference"),
        t("tab_governance"),
        t("tab_tech_details"),
    ])

    with tabs[0]:
        information_panel(t("tab_product_overview"), t("dsf_product_overview_desc"))
        if v1_metrics:
            kpi_grid([
                (t("dsf_v1_champion_f1"), f"{v1_metrics.get('f1', 0):.4f}", t("dsf_v1_champion_f1_desc")),
                (t("dsf_v4_hybrid_rrf_ndcg"), f"{v5_results.get('holdout_hybrid_rrf_ndcg@10', 0):.4f}" if v5_results else "—", t("dsf_v4_hybrid_rrf_desc")),
                (t("dsf_v5_cross_encoder_ndcg"), f"{v5_results.get('holdout_blended_ndcg@10', 0):.4f}" if v5_results else "—", t("dsf_v5_ce_desc")),
                (t("governance"), t("not_production_promoted"), t("best_reranking_candidate")),
            ])

    with tabs[1]:
        information_panel(t("tab_data_foundation"), t("dsf_data_foundation_desc"))
        section_heading(t("dsf_key_schema_fields"))
        st.markdown("- **item_id** — product identifier\n"
                    "- **title** — product title (Turkish)\n"
                    "- **category** — category path\n"
                    "- **brand** — brand name\n"
                    "- **gender / age_group** — demographic targeting\n"
                    "- **attributes** — key-value product attributes\n"
                    "- **query** — user search query\n"
                    "- **label** — binary relevance (0/1)\n"
                    "- **sample_weight** — importance weight for learning")

    with tabs[2]:
        section_heading(t("tab_system_evolution"))
        st.markdown(
            "- **V1** — TF-IDF relevance classification (Logistic Regression). Verified champion, F1 ≈ 0.83.\n"
            "- **V2** — Challenger model research (tree-based, linear SVM). Historical, not promoted.\n"
            "- **V2.1** — Robust repeated-seed evaluation framework. Completed research.\n"
            "- **V3 / V3.1** — Semantic retrieval (TF-IDF + BM25 + sentence transformers). Hybrid RRF k=20 fusion.\n"
            "- **V4** — End-to-end pipeline: retrieval → hybrid RRF fusion → cross-encoder reranking. Deterministic tie-breaking.\n"
            "- **V5** — Pure cross-encoder reranking (mmarco-mMiniLMv2-L12-H384). Alpha=1.0, title_compact_metadata, pool 20, batch 8. "
            "Holdout NDCG@10 0.6785 vs 0.6191 baseline (+10.8%). Governance: Best Reranking Research Candidate, Not Production Promoted."
        )

    with tabs[3]:
        information_panel(t("tab_retrieval_arch"), t("dsf_retrieval_arch_desc"))
        if v5_results:
            evidence_strip([
                ("Retrieval Policy", "Hybrid RRF k=20", "Bounded candidate generation"),
                ("Semantic Index", "sentence-transformers", "FAISS/HNSW, persisted"),
                ("Fallback", "Retrieval-only", "Explicit, no score fabrication"),
            ])

    with tabs[4]:
        information_panel(t("tab_ranking_reranking"), t("dsf_ranking_reranking_desc"))
        if v5_results:
            evidence_strip([
                ("Model", "mmarco-mMiniLMv2", "Apache-2.0, CPU"),
                ("Policy", "Cross-Encoder (alpha=1.0)", "No lexical weight"),
                ("Variant", "title_compact_metadata", "Title + category + brand + attrs"),
            ])

    with tabs[5]:
        section_heading(t("tab_evaluation"))
        if v5_results:
            baseline = v5_results.get("holdout_hybrid_rrf_ndcg@10", 0)
            v5_ndcg = v5_results.get("holdout_blended_ndcg@10", 0)
            delta = v5_results.get("holdout_ndcg_absolute_delta", 0)
            rel_pct = v5_results.get("holdout_ndcg_relative_pct_vs_hybrid", 0)
            kpi_grid([
                (t("dsf_eval_hybrid_rrf_label"), f"{baseline:.4f}", t("dsf_eval_hybrid_rrf_desc")),
                (t("dsf_eval_ce_label"), f"{v5_ndcg:.4f}", t("dsf_eval_ce_desc")),
                (t("dsf_eval_absolute_delta"), f"+{delta:.4f}", f"Relative: +{rel_pct:.1f}%"),
                (t("dsf_eval_queries_label"), str(v5_results.get("holdout_query_count", 150)), t("dsf_eval_queries_desc")),
            ])
            section_heading(t("tab_governance"))
            st.info("Best Reranking Research Candidate · Not Production Promoted. "
                    "The cross-encoder reranker improved NDCG@10 on the frozen 150-query V5 holdout. "
                    "It is an experimental reranker on a bounded demo; no production SLA or business impact is claimed.")
        else:
            st.warning("V5 results not available. Run offline evaluation to generate.")

    with tabs[6]:
        information_panel(t("tab_live_inference"), t("dsf_live_inference_desc"))
        evidence_strip([
            ("Cold Load", "~3–5 s", "Tokenizer + model"),
            ("Warm p95", "~200 ms", "Pool 20, batch 8, CPU"),
            ("Fallback", "Retrieval-only", "No fabricated scores"),
        ])

    with tabs[7]:
        information_panel(t("tab_governance"), t("dsf_governance_desc"))
        section_heading(t("deployment_readiness_title"))
        kpi_grid([
            (t("dsf_deploy_streamlit_cloud"), t("ready_status"), t("dsf_deploy_streamlit_cloud_desc")),
            (t("dsf_deploy_model_serving"), t("research_status"), t("dsf_deploy_model_serving_desc")),
            (t("dsf_deploy_ab_testing"), t("roadmap_status"), t("dsf_deploy_ab_testing_desc")),
            (t("capability_horizontal_scaling"), t("roadmap_status"), t("dsf_deploy_horizontal_scaling_desc")),
        ])

    with tabs[8]:
        section_heading(t("tab_tech_details"))
        st.markdown(
            "- **Pipeline**: retrieval (lexical + semantic) → RRF fusion → cross-encoder rerank → deterministic ranking\n"
            "- **Model revisions**: pinned via HuggingFace `revision` parameter\n"
            "- **Evaluation**: 150 frozen queries, seed 42, paired bootstrap 95% CI\n"
            "- **Latency**: warm p95 ~200ms (pool 20, batch 8, CPU); cold ~3-5s\n"
            "- **Artifacts**: all paths relative to repository root, no absolute paths in UI\n"
            "- **Error handling**: explicit fallbacks, no silent failures\n"
            "- **Localization**: Turkish / English via i18n keys"
        )
        for name in ["PROJECT_PLAN.md", "EXPERIMENT_PLAN.md", "DATA_DICTIONARY.md",
                     "MODEL_CARD_TEMPLATE.md", "RISK_AND_LIMITATIONS.md", "DEPLOYMENT_PLAN.md"]:
            with st.expander(name, expanded=False):
                st.markdown(load_text_safe(str(DATA_SCIENCE_FINAL_DIR / name)))

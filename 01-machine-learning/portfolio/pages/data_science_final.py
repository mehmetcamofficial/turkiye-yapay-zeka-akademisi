"""Trendyol Search Relevance & Ranking System - completed V1 through V5."""

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
        title="Trendyol Search Relevance & Ranking System",
        subtitle=t("subtitle_data_science_final"),
        kicker=t("section_search"),
    )
    st.markdown(status_badge(item["status"]), unsafe_allow_html=True)

    v5_results = load_json_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_results.json"))
    v1_metrics = load_json_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "metrics.json"))

    tabs = st.tabs([
        "Product Overview",
        "Data Foundation",
        "System Evolution",
        "Retrieval Architecture",
        "Ranking & Reranking",
        "Evaluation",
        "Live Inference",
        "Governance",
        "Technical Details",
    ])

    with tabs[0]:
        information_panel("Product Overview",
            "A production-grade search intelligence platform for e-commerce relevance and ranking. "
            "The system evolves from a verified V1 TF-IDF classifier through semantic retrieval (V3), "
            "hybrid RRF fusion (V4), to cross-encoder reranking (V5) with offline validation on 150 frozen queries.")
        if v1_metrics:
            kpi_grid([
                ("V1 Champion F1", f"{v1_metrics.get('f1', 0):.4f}", "TF-IDF + Logistic Regression"),
                ("V4 Hybrid RRF NDCG@10", f"{v5_results.get('holdout_hybrid_rrf_ndcg@10', 0):.4f}" if v5_results else "—", "Lexical + semantic fusion"),
                ("V5 Cross-Encoder NDCG@10", f"{v5_results.get('holdout_blended_ndcg@10', 0):.4f}" if v5_results else "—", "Pure CE reranking"),
                ("Governance", "Not Production Promoted", "Best Reranking Research Candidate"),
            ])

    with tabs[1]:
        information_panel("Data Foundation",
            "TEKNOFEST Trendyol 2026 Datathon dataset: 962K+ products, 50K+ queries, 250K+ labeled pairs. "
            "Schema includes item_id, title, category, brand, gender, age_group, attributes, query, label, sample_weight. "
            "Transactional columns (order, payment, customer) are absent by design — this is a search relevance dataset.")
        section_heading("Key Schema Fields")
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
        section_heading("System Evolution")
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
        information_panel("Retrieval Architecture",
            "Two-stage: candidate generation (bounded pool 20) → reranking. "
            "Lexical: TF-IDF + BM25. Semantic: sentence-transformers embeddings with FAISS/HNSW index. "
            "Hybrid fusion: Reciprocal Rank Fusion (RRF) with k=20, deterministic tie-breaking by item_id. "
            "Retrieval-only fallback on reranker failure (explicit degradation, no fabricated scores).")
        if v5_results:
            evidence_strip([
                ("Retrieval Policy", "Hybrid RRF k=20", "Bounded candidate generation"),
                ("Semantic Index", "sentence-transformers", "FAISS/HNSW, persisted"),
                ("Fallback", "Retrieval-only", "Explicit, no score fabrication"),
            ])

    with tabs[4]:
        information_panel("Ranking & Reranking",
            "V4: Hybrid RRF fusion → LightGBM ranker (experimental). "
            "V5: Pure cross-encoder reranking on bounded pool. "
            "Model: mmarco-mMiniLMv2-L12-H384 (Apache-2.0). Alpha=1.0 (pure CE). "
            "Document variant: title_compact_metadata. Batch size: 8. CPU inference.")
        if v5_results:
            evidence_strip([
                ("Model", "mmarco-mMiniLMv2", "Apache-2.0, CPU"),
                ("Policy", "Cross-Encoder (alpha=1.0)", "No lexical weight"),
                ("Variant", "title_compact_metadata", "Title + category + brand + attrs"),
            ])

    with tabs[5]:
        section_heading("Offline Evaluation")
        if v5_results:
            baseline = v5_results.get("holdout_hybrid_rrf_ndcg@10", 0)
            v5_ndcg = v5_results.get("holdout_blended_ndcg@10", 0)
            delta = v5_results.get("holdout_ndcg_absolute_delta", 0)
            rel_pct = v5_results.get("holdout_ndcg_relative_pct_vs_hybrid", 0)
            kpi_grid([
                ("Hybrid RRF NDCG@10", f"{baseline:.4f}", "Baseline (pool 20)"),
                ("Cross-Encoder NDCG@10", f"{v5_ndcg:.4f}", "Selected policy"),
                ("Absolute Δ", f"+{delta:.4f}", f"Relative: +{rel_pct:.1f}%"),
                ("Queries", str(v5_results.get("holdout_query_count", 150)), "Frozen holdout, seed 42"),
            ])
            section_heading("Governance Decision")
            st.info("Best Reranking Research Candidate · Not Production Promoted. "
                    "The cross-encoder reranker improved NDCG@10 on the frozen 150-query V5 holdout. "
                    "It is an experimental reranker on a bounded demo; no production SLA or business impact is claimed.")
        else:
            st.warning("V5 results not available. Run offline evaluation to generate.")

    with tabs[6]:
        information_panel("Live Inference",
            "The Trendyol V5 page provides an interactive cross-encoder reranking demo on a bounded 5,000-product catalogue. "
            "Lazy model loading, cold-start ~several seconds, warm latency p95 ≈ 200ms (pool 20, CPU). "
            "Fallback to retrieval-only on CE failure.")
        evidence_strip([
            ("Cold Load", "~3–5 s", "Tokenizer + model"),
            ("Warm p95", "~200 ms", "Pool 20, batch 8, CPU"),
            ("Fallback", "Retrieval-only", "No fabricated scores"),
        ])

    with tabs[7]:
        information_panel("Governance",
            "Model lineage: HuggingFace revision-pinned (immutable). "
            "Artifact registry: metadata-driven from persisted outputs. "
            "Evaluation: champion/challenger with paired bootstrap CI. "
            "Deployment: Streamlit Community Cloud compatible (lazy load, bounded data). "
            "Status: Research candidate only. No production endpoint, auth, monitoring, or A/B framework deployed.")
        section_heading("Deployment Readiness")
        kpi_grid([
            ("Streamlit Cloud", "Ready", "Unified bilingual app, pinned deps"),
            ("Model Serving", "Research", "No REST API, no auth, no monitoring"),
            ("A/B Testing", "Roadmap", "Framework not implemented"),
            ("Horizontal Scaling", "Roadmap", "Stateless design, needs orchestration"),
        ])

    with tabs[8]:
        section_heading("Technical Details")
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

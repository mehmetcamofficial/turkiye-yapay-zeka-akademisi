from __future__ import annotations

import json
import time
from html import escape
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.i18n import t
from portfolio.trendyol_v5_pipeline_service import v5_search, v5_load_counters, load_frozen_policy
from portfolio.ui_components import (
    format_latency_ms, format_ranking_metric, hero_panel,
    information_panel, render_safe_table, section_heading,
)

PRESETS = [
    "kablosuz kulaklık", "beyaz kadın sneaker", "çocuk yağmurluk",
    "erkek siyah pantolon", "güneş gözlüğü", "telefon hızlı şarj adaptörü",
    "su geçirmez erkek mont", "iphone 15 pro max kılıf",
    "500 ml şampuan", "küçük ırk köpek maması",
]


def render() -> None:
    hero_panel(
        title=t("nav_live_inference"),
        subtitle=t("subtitle_live_inference"),
        kicker=t("section_search"),
    )

    frozen = load_frozen_policy()

    def _hc(title_key: str, value: str, detail: str = "") -> str:
        return (
            f'<div class="health-card" tabindex="0">'
            f'<div class="health-card-header">'
            f'<span class="health-dot health-dot-ready"></span>'
            f'<span class="health-card-title">{escape(t(title_key))}</span>'
            f'</div>'
            f'<div class="health-card-status" {"style=word-break:break-all" if title_key in ("model_label", "document_variant_label") else ""}>{escape(value)}</div>'
            f'{f"<div class=health-card-detail>{escape(detail)}</div>" if detail else ""}'
            f'</div>'
        )

    st.markdown(
        f'<div class="health-grid">'
        + "".join([
            _hc("policy_label", frozen.get("policy", "cross_encoder")),
            _hc("model_label", frozen.get("model_id", "—").split("/")[-1]),
            _hc("alpha_label", f"{frozen.get('alpha', 1.0):.2f}"),
            _hc("candidate_pool_label", str(frozen.get("candidate_pool", 20))),
            _hc("batch_size_label", str(frozen.get("batch_size", 8))),
            _hc("document_variant_label", frozen.get("document_variant", "title_compact_metadata")),
        ])
        + '</div>',
        unsafe_allow_html=True,
    )

    information_panel(t("cold_start_title"), t("cold_start_warning"))

    preset = st.selectbox(t("preset_query"), PRESETS, key="live_preset")
    query = st.text_input(t("query_label"), preset, key="live_query")
    if st.button(t("run_inference"), key="live_run"):
        started = time.perf_counter()
        response = v5_search(query=query)
        total_ms = (time.perf_counter() - started) * 1000.0
        if response.get("success"):
            results = response.get("results", [])
            st.markdown(
                f'<div style="display:flex;gap:1rem;align-items:center;margin:0.5rem 0">'
                f'<span class="badge badge-available">{escape(str(len(results)))} products</span>'
                f'<span style="color:var(--muted);font-size:0.82rem">{escape(f"{total_ms:.0f}")} ms total</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            stage = response.get("stage_metrics", {})
            xs = stage.get("cross_encoder_ms")
            if xs is not None:
                st.caption(f"Cross-encoder scoring: {xs:.1f} ms")
            display = []
            for r in results:
                display.append({
                    t("rank_label"): r.get("final_rank", r.get("cross_encoder_rank", "—")),
                    t("product_label"): r.get("title", "—"),
                    t("category"): r.get("category", "—"),
                    t("brand"): r.get("brand", "—"),
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

    information_panel(
        t("limitations"),
        t("live_inference_limitations"),
    )

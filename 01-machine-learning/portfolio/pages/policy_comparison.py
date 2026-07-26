from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe
from portfolio.ui_components import (
    decision_banner, evidence_strip, format_delta, format_latency_ms,
    format_ranking_metric, hero_panel, kpi_grid, render_safe_table, section_heading,
)


def _load_results() -> dict:
    path = TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_results.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def _load_paired() -> dict | list:
    return load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_paired_bootstrap.csv"))


def render() -> None:
    hero_panel(
        title=t("nav_policy_comparison"),
        subtitle=t("subtitle_policy_comparison"),
        kicker=t("section_search"),
    )

    results = _load_results()
    if not results:
        st.warning(t("v5_results_unavailable"))
        return

    v4_ndcg = results.get("v4_aggregate_hybrid_rrf_ndcg@10", "—")
    v5_hybrid_ndcg = results.get("holdout_hybrid_rrf_ndcg@10", "—")
    v5_ce_ndcg = results.get("holdout_blended_ndcg@10", "—")
    delta = results.get("holdout_ndcg_absolute_delta", "—")
    rel_pct = results.get("holdout_ndcg_relative_pct_vs_hybrid", "—")

    evidence_strip([
        ("V4 Hybrid RRF NDCG@10", format_ranking_metric(v4_ndcg), "Aggregate holdout"),
        ("V5 Baseline (Hybrid RRF) NDCG@10", format_ranking_metric(v5_hybrid_ndcg), "Baseline"),
        ("V5 Cross-Encoder NDCG@10", format_ranking_metric(v5_ce_ndcg), "Selected policy"),
        ("Absolute Gain", format_delta(delta), f"Relative: +{rel_pct:.1f}%" if isinstance(rel_pct, float) else ""),
    ])

    section_heading(t("paired_bootstrap_results"), t("paired_bootstrap_desc"))
    paired = _load_paired()
    if not paired.empty:
        display = paired[paired.metric.isin(["ndcg@10", "mrr"])][
            ["candidate", "metric", "delta", "ci_low", "ci_high", "improved", "unchanged", "worsened"]
        ].copy()
        display.columns = [
            t("candidate_col"), t("metric_col"), t("delta_col"),
            t("ci_low_col"), t("ci_high_col"),
            t("improved_col"), t("unchanged_col"), t("worsened_col"),
        ]
        render_safe_table(display, max_rows=10)

    improved = results.get("holdout_improved", 0)
    unchanged = results.get("holdout_unchanged", 0)
    worsened = results.get("holdout_worsened", 0)

    if v4_ndcg and isinstance(v5_ce_ndcg, (int, float)):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3))
        metrics = ["NDCG@10", "MRR"]
        v4_vals = [v4_ndcg, results.get("v4_aggregate_hybrid_rrf_mrr", 0)]
        v5_vals = [v5_ce_ndcg, results.get("holdout_blended_mrr", 0)]
        x = np.arange(len(metrics))
        width = 0.3
        bars1 = ax1.bar(x - width / 2, v4_vals, width, label="V4 Hybrid", color="#94a3b8")
        bars2 = ax1.bar(x + width / 2, v5_vals, width, label="V5 Cross-Encoder", color="#22c55e")
        for bar in bars1:
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                     f"{bar.get_height():.4f}", ha="center", fontsize=7)
        for bar in bars2:
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                     f"{bar.get_height():.4f}", ha="center", fontsize=7)
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
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, str(v), ha="center", fontsize=9)
        ax2.set_title(t("query_impact"), fontsize=10)
        ax2.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        st.pyplot(fig)

    decision_banner(
        t("best_reranking_candidate") + " · " + t("not_production_promoted"),
        t("not_production_promoted_desc"),
    )

    section_heading(t("holdout_detail"), t("holdout_detail_desc"))
    holdout = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_holdout_summary.csv"))
    if not holdout.empty:
        display = holdout[["policy", "ndcg@10_mean", "mrr_mean", "candidate_recall@20_mean"]].copy()
        display.columns = [t("policy_col"), t("ndcg10_col"), t("mrr_col"), t("candidate_recall20_col")]
        render_safe_table(display, max_rows=10)

    cols = st.columns(3)
    with cols[0]:
        st.metric("Total Queries", str(results.get("holdout_query_count", "—")))
    with cols[1]:
        ndcg_ci = results.get("holdout_ndcg_ci95", [])
        if ndcg_ci:
            st.info(f"NDCG@10 95% CI: [{format_ranking_metric(ndcg_ci[0])}, {format_ranking_metric(ndcg_ci[1])}]")
    with cols[2]:
        mrr_ci = results.get("holdout_mrr_ci95", [])
        if mrr_ci:
            st.caption(f"MRR 95% CI: [{format_ranking_metric(mrr_ci[0])}, {format_ranking_metric(mrr_ci[1])}]")

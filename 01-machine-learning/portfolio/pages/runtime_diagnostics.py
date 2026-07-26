from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe
from portfolio.ui_components import hero_panel, render_safe_table, section_heading


def _load_v5_results():
    path = TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_results.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def render() -> None:
    hero_panel(
        title=t("nav_runtime_diagnostics"),
        subtitle=t("subtitle_runtime_diagnostics"),
        kicker=t("section_search"),
    )

    results = _load_v5_results()

    section_heading(t("latency_benchmarks"), t("latency_benchmarks_desc"))
    if results:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(t("mean_warm_latency"), f"{results.get('pool20_warm_latency_mean_ms', 0):.1f}" if isinstance(results.get('pool20_warm_latency_mean_ms'), (int, float)) else "—")
        col2.metric(t("p50_warm_latency"), f"{results.get('pool20_warm_latency_p50_ms', 0):.1f}" if isinstance(results.get('pool20_warm_latency_p50_ms'), (int, float)) else "—")
        col3.metric(t("p95_warm_latency"), f"{results.get('pool20_warm_latency_p95_ms', 0):.1f}" if isinstance(results.get('pool20_warm_latency_p95_ms'), (int, float)) else "—")
        col4.metric(t("cold_load"), f"{results.get('cold_tokenizer_model_load_seconds', 0):.2f}" if isinstance(results.get('cold_tokenizer_model_load_seconds'), (int, float)) else "—")

        warm_ms = results.get("pool20_warm_latency_mean_ms")
        cold_s = results.get("cold_tokenizer_model_load_seconds")
        if warm_ms and cold_s:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(6, 2.5))
            labels = [t("cold_start"), t("warm_inference")]
            times = [cold_s * 1000, warm_ms]
            bars = ax.bar(labels, times, color=["#ef4444", "#22c55e"], width=0.4)
            for bar, v in zip(bars, times):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                        f"{v:.0f} ms", ha="center", fontsize=9)
            ax.set_ylabel(t("latency_ms"))
            ax.set_title(t("latency_breakdown"), fontsize=10)
            fig.tight_layout()
            st.pyplot(fig)

    section_heading(t("pool_benchmark"), t("pool_benchmark_desc"))
    pool = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_pool_benchmark.csv"))
    if not pool.empty:
        if "candidate_pool_size" in pool and "latency_mean_ms" in pool:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(6, 2.5))
            ax.plot(pool["candidate_pool_size"], pool["latency_mean_ms"], marker="o", color="#6366f1")
            ax.set_xlabel(t("candidate_pool_label"))
            ax.set_ylabel(t("latency_ms"))
            ax.set_title(t("latency_vs_pool"), fontsize=10)
            fig.tight_layout()
            st.pyplot(fig)
        render_safe_table(pool, max_rows=10)

    section_heading(t("batch_benchmark"), t("batch_benchmark_desc"))
    batch = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_batch_benchmark.csv"))
    if not batch.empty:
        render_safe_table(batch, max_rows=10)

    section_heading(t("cold_start_details"), t("cold_start_details_desc"))
    if results:
        st.metric(t("model_load_count_label"), results.get("model_load_count", "—"))
        st.metric(t("tokenizer_load_count_label"), results.get("tokenizer_load_count", "—"))
        st.metric(t("device_col"), results.get("device", "cpu"))

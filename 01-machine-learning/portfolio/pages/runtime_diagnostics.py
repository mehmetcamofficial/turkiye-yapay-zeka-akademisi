from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe
from portfolio.ui_components import hero_panel, render_safe_table, section_heading
from portfolio.trendyol_v5_pipeline_service import v5_load_counters


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
    counters = v5_load_counters()
    model_loaded = bool(counters.get("model_loaded"))
    model_load_count = counters.get("model_load_count", 0)
    tokenizer_load_count = counters.get("tokenizer_load_count", 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("model_load_count_label"), f"{model_load_count} {t('unit_times')}",
              help=t("model_load_expected"))
    c2.metric(t("tokenizer_load_count_label"), f"{tokenizer_load_count} {t('unit_times')}",
              help=t("tokenizer_no_reload"))
    c3.metric(t("device_col"), t("cpu_label"), help=t("cpu_inference"))
    cache_status = t("cache_active") if model_loaded else t("cache_cold")
    c4.metric(t("cache_status_label"), cache_status,
              help=t("cache_reusable") if model_loaded else t("cache_first_use"))

    section_heading(t("runtime_lifecycle"), t("runtime_lifecycle_desc"))
    stages = [
        (t("stage_first_request"), model_loaded),
        (t("stage_tokenizer_load"), model_loaded),
        (t("stage_model_load"), model_loaded),
        (t("stage_cache"), model_loaded),
        (t("stage_warm_inference"), model_loaded),
    ]
    stage_text = " \u2192 ".join(
        f"**{label}**" if active else label
        for label, active in stages
    )
    st.markdown(stage_text)
    if not model_loaded:
        st.caption(t("lifecycle_cold_hint"))

    section_heading(t("latency_benchmarks"), t("latency_benchmarks_desc"))
    if results:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("cold_start"), f"{results.get('cold_tokenizer_model_load_seconds', 0):.2f} s"
                  if isinstance(results.get('cold_tokenizer_model_load_seconds'), (int, float)) else "\u2014")
        c2.metric(t("mean_warm_latency"), f"{results.get('pool20_warm_latency_mean_ms', 0):.1f} ms"
                  if isinstance(results.get('pool20_warm_latency_mean_ms'), (int, float)) else "\u2014")
        c3.metric(t("p50_warm_latency"), f"{results.get('pool20_warm_latency_p50_ms', 0):.1f} ms"
                  if isinstance(results.get('pool20_warm_latency_p50_ms'), (int, float)) else "\u2014")
        c4.metric(t("p95_warm_latency"), f"{results.get('pool20_warm_latency_p95_ms', 0):.1f} ms"
                  if isinstance(results.get('pool20_warm_latency_p95_ms'), (int, float)) else "\u2014")

        warm_ms = results.get("pool20_warm_latency_mean_ms")
        cold_s = results.get("cold_tokenizer_model_load_seconds")
        if warm_ms and cold_s:
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
    else:
        st.caption(t("runtime_metrics_unavailable"))

    st.info(f"**{t('explain_what')}**\n\n{t('explain_what_desc')}")
    st.info(f"**{t('explain_why')}**\n\n{t('explain_why_desc')}")
    st.info(f"**{t('explain_limitation')}**\n\n{t('explain_limitation_desc')}")

    section_heading(t("runtime_matrix"), t("runtime_matrix_desc"))
    matrix_rows = []
    components = [
        ("Tokenizer", tokenizer_load_count, "CPU", "\u2014"),
        ("Cross-Encoder", model_load_count, "CPU",
         f"{results.get('pool20_warm_latency_mean_ms', '\u2014')} ms" if results else "\u2014"),
    ]
    if results:
        idx_load = results.get("index_load_count", model_load_count)
        components.append(("Candidate Index", idx_load, "CPU", "\u2014"))
    for name, load_count, device, latency in components:
        status = t("status_ready") if load_count > 0 else t("status_cold")
        matrix_rows.append({
            t("component_col"): name,
            t("status_col"): status,
            t("load_count_col"): f"{load_count}",
            t("device_col_short"): device,
            t("latest_latency_col"): latency,
        })
    if matrix_rows:
        render_safe_table(pd.DataFrame(matrix_rows), max_rows=10)

    section_heading(t("pool_benchmark"), t("pool_benchmark_desc"))
    pool = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "v5" / "v5_pool_benchmark.csv"))
    if not pool.empty:
        if "candidate_pool_size" in pool and "latency_mean_ms" in pool:
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

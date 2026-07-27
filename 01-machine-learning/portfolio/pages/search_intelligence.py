from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from portfolio.config import ML_ROOT
from portfolio.i18n import t
from portfolio.search_index import get_search_index
from portfolio.ui_components import hero_panel, section_heading, render_safe_table

EVAL_DIR = ML_ROOT / "evaluation" / "search"
GOLDEN_PATH = EVAL_DIR / "golden_queries.yaml"
BASELINE_PATH = EVAL_DIR / "baselines" / "milestone_3_1.json"
QUALITY_GATES_PATH = EVAL_DIR / "quality_gates.yaml"

METRIC_LABELS: dict[str, dict[str, str]] = {
    "ndcg@10": {"title": "NDCG@10", "subtitle": "Ranking Quality", "direction": "higher is better",
                "gate_key": "ndcg@10"},
    "mrr": {"title": "MRR", "subtitle": "First Relevant Result", "direction": "higher is better",
            "gate_key": "mrr"},
    "precision@10": {"title": "Precision@10", "subtitle": "Top-10 Precision", "direction": "higher is better",
                     "gate_key": "precision@10"},
    "recall@10": {"title": "Recall@10", "subtitle": "Top-10 Recall", "direction": "higher is better",
                  "gate_key": "recall@10"},
    "relevant_query_coverage": {"title": "Relevant Query Coverage", "subtitle": "Queries With Relevant Results",
                                "direction": "higher is better", "gate_key": "relevant_query_coverage"},
    "result_query_coverage": {"title": "Result Coverage", "subtitle": "Queries Returning Any Result",
                              "direction": "higher is better", "gate_key": "result_query_coverage"},
    "must_include_success_rate": {"title": "Must-Include Success", "subtitle": "Required Resources Found",
                                  "direction": "higher is better", "gate_key": "must_include_success_rate"},
}

LEGACY_METRIC_MAP = {
    "query_coverage": "relevant_query_coverage",
}


def _load_json(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _format_score(score: float) -> str:
    if isinstance(score, float):
        return f"{score:.4f}"
    return str(score)


def _schema_version(artifact: dict[str, Any]) -> int:
    return artifact.get("schema_version", 1)


def _normalize_metrics(metrics: dict[str, Any], artifact_schema: int) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, label_info in METRIC_LABELS.items():
        if key in metrics:
            val = metrics[key]
            result[key] = {"value": val, "present": True, "note": ""}
        elif artifact_schema == 1 and key in LEGACY_METRIC_MAP.values():
            old_key = next(k for k, v in LEGACY_METRIC_MAP.items() if v == key)
            if old_key in metrics:
                result[key] = {"value": metrics[old_key], "present": True,
                               "note": "mapped from legacy key"}
            else:
                result[key] = {"value": None, "present": False, "note": "Not available in legacy baseline"}
        elif key == "result_query_coverage" and artifact_schema == 1:
            result[key] = {"value": None, "present": False,
                           "note": "Not available in legacy baseline"}
        else:
            result[key] = {"value": None, "present": False, "note": "Key not in artifact"}
    return result


def _run_evaluation(top_k: int = 10) -> dict[str, Any]:
    from evaluation.search.evaluator import SearchEvaluator

    index = get_search_index()
    index.ensure_ready()

    def search_fn(query: str, top_k: int = 10):
        return index.search(query, top_k=top_k)

    evaluator = SearchEvaluator(search_fn=search_fn, golden_path=GOLDEN_PATH, top_k=top_k)
    return evaluator.run()


def _metric_status(value: float | None, present: bool, threshold: float | None, gate_metric: str) -> str:
    if not present or value is None:
        return "DATA MISSING"
    if threshold is not None:
        if value >= threshold:
            return "PASS"
        else:
            return "FAIL"
    return "NOT EVALUATED"


def _render_search_health_header(metrics_info: dict[str, dict[str, Any]],
                                  gates_cfg: list[dict[str, Any]]) -> None:
    total_gates = len(gates_cfg) if gates_cfg else 0
    passing_gates = 0
    for gate_cfg in gates_cfg:
        g_metric = gate_cfg["metric"]
        minfo = metrics_info.get(g_metric, {})
        if minfo.get("present") and minfo.get("value") is not None:
            val = minfo["value"]
            threshold = gate_cfg["threshold"]
            if val >= threshold:
                passing_gates += 1

    missing = sum(1 for gate_cfg in gates_cfg
                  if not metrics_info.get(gate_cfg["metric"], {}).get("present"))
    total_gates_effective = sum(1 for gate_cfg in gates_cfg
                                if metrics_info.get(gate_cfg["metric"], {}).get("present"))

    if missing > 0:
        summary_status = "Evaluation Data Incomplete"
    elif passing_gates == total_gates_effective:
        summary_status = "Healthy"
    else:
        summary_status = "Needs Attention"

    cols = st.columns(4)
    cols[0].metric("Search Health", summary_status)
    cols[1].metric("Gates Passing", f"{passing_gates} / {total_gates_effective}")
    if missing > 0:
        cols[2].metric("Missing Metrics", str(missing))
    cols[3].metric("Total Gates", str(total_gates))


def _render_metrics_panel(metrics: dict[str, Any], artifact_schema: int,
                          gates_cfg: list[dict[str, Any]]) -> None:
    metrics_info = _normalize_metrics(metrics, artifact_schema)

    gate_map: dict[str, dict[str, Any]] = {}
    for gc in gates_cfg:
        gate_map[gc["metric"]] = gc

    html = ""
    for key, label_info in METRIC_LABELS.items():
        minfo = metrics_info.get(key, {"value": None, "present": False, "note": ""})
        value = minfo["value"]
        present = minfo["present"]
        note = minfo["note"]
        gate = gate_map.get(key)
        threshold = gate["threshold"] if gate else None
        status = _metric_status(value, present, threshold, key)

        if present and value is not None:
            display_val = f"{value:.4f}"
        else:
            display_val = "Data unavailable"

        gate_info = ""
        tooltip = ""
        if gate:
            gate_info = f"{gate['operator']} {gate['threshold']}"
            tooltip = f"{label_info['title']}: {gate_info} ({label_info['direction']})"

        status_css = {
            "PASS": "metric-pass",
            "FAIL": "metric-fail",
            "DATA MISSING": "metric-missing",
            "NOT EVALUATED": "metric-na",
        }.get(status, "metric-na")

        html += f"""
        <div class="sh-metric-card {status_css} tooltip-trigger">
          {f'<div class="tooltip-content">{tooltip}</div>' if tooltip else ''}
          <div class="sh-metric-top">
            <span class="sh-metric-title">{label_info['title']}</span>
            <span class="sh-status-badge sh-{status.lower().replace(' ', '-')}">{status}</span>
          </div>
          <div class="sh-metric-subtitle">{label_info['subtitle']}</div>
          <div class="sh-metric-value">{display_val}</div>
          <div class="sh-metric-meta">
            <span class="sh-metric-direction">{label_info['direction']}</span>
            {f'<span class="sh-metric-gate">Gate: {gate_info}</span>' if gate_info else ''}
          </div>
          {f'<div class="sh-metric-note">{note}</div>' if note else ''}
        </div>"""

    st.markdown(f'<div class="sh-metrics-grid">{html}</div>', unsafe_allow_html=True)


def _render_gates_panel(metrics: dict[str, Any], artifact_schema: int,
                        dataset_label: str, query_count: int) -> None:
    from evaluation.search.dataset import load_quality_gates
    from evaluation.search.schema import QualityGate

    gates_config = load_quality_gates(QUALITY_GATES_PATH)
    raw_gates = gates_config.get("gates", [])
    if not raw_gates:
        st.info(t("si_gates_not_configured"))
        return

    metrics_info = _normalize_metrics(metrics, artifact_schema)

    gate_map: dict[str, dict[str, Any]] = {}
    for gc in raw_gates:
        gate_map[gc["metric"]] = gc

    rows = []
    for gate_cfg in raw_gates:
        gate = QualityGate(
            metric=gate_cfg["metric"],
            operator=gate_cfg["operator"],
            threshold=gate_cfg["threshold"],
            description=gate_cfg.get("description", ""),
        )
        minfo = metrics_info.get(gate.metric, {"value": None, "present": False, "note": ""})
        value = minfo["value"]
        present = minfo["present"]
        note = minfo["note"]
        threshold = gate_cfg["threshold"]

        gate_status, gate_msg = gate.evaluate_with_status(value, metric_present=present)

        explanation = gate_msg
        if note:
            explanation = note
        if gate_status == "SKIPPED_MISSING_METRIC":
            explanation = f"{gate.metric}: missing in artifact ({dataset_label})"

        rows.append({
            "Gate": METRIC_LABELS.get(gate.metric, {}).get("title", gate.metric),
            "Required": f"{gate.operator} {threshold}",
            "Observed": _format_score(value) if present and value is not None else "—",
            "Status": gate_status,
            "Explanation": explanation,
        })

    col1, col2 = st.columns(2)
    with col1:
        st.metric(t("si_dataset"), dataset_label)
    with col2:
        st.metric(t("si_queries"), str(query_count))

    display = pd.DataFrame(rows)
    render_safe_table(display, max_rows=20)

    status_summary = display["Status"].value_counts().to_dict()
    failures = status_summary.get("FAIL", 0)
    missing = status_summary.get("SKIPPED_MISSING_METRIC", 0)
    if failures > 0:
        st.error(t("si_some_gates_fail"))
    elif missing > 0:
        st.info(t("si_gates_skip"))
    else:
        st.success(t("si_all_gates_pass"))


def _render_query_breakdown(per_query: dict[str, Any]) -> None:
    section_heading(t("si_per_query"))
    rows = []
    for q, data in sorted(per_query.items()):
        retrieved = data.get("result_ids", data.get("retrieved", []))
        expected = data.get("expected", [])
        hits = sum(1 for r in retrieved if r in expected)
        intent = data.get("intent", "")
        rows.append({
            "Query": q,
            "Intent": intent,
            "Retrieved": len(retrieved),
            "Expected": len(expected),
            "Hits": hits,
        })
    if rows:
        render_safe_table(pd.DataFrame(rows), max_rows=50)


def _render_baseline_comparison() -> None:
    baseline = _load_json(BASELINE_PATH)
    if not baseline or not baseline.get("metrics"):
        st.info(t("si_no_baseline"))
        return

    baseline_schema = _schema_version(baseline)
    baseline_query_count = baseline.get("total_queries", 0)
    baseline_metrics = baseline.get("metrics", {})

    gates_config_raw = _load_json(str(QUALITY_GATES_PATH).replace(".json", ".yaml"))
    if not gates_config_raw:
        from evaluation.search.dataset import load_quality_gates
        gates_config_raw = load_quality_gates(QUALITY_GATES_PATH)
    raw_gates = gates_config_raw.get("gates", [])

    st.markdown(f"""
    <div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:1rem;">
      <div class="status-strip-item">
        <span class="status-strip-label">Historical Baseline</span>
        <span class="status-strip-value">{baseline_query_count} queries</span>
        <span class="status-strip-sub">Schema v{baseline_schema} · {baseline.get('timestamp','N/A')[:10]}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    section_heading(t("si_baseline_metrics"))
    _render_metrics_panel(baseline_metrics, baseline_schema, raw_gates)
    _render_gates_panel(baseline_metrics, baseline_schema,
                        f"Legacy Baseline v{baseline_schema}", baseline_query_count)


def _render_version_evolution() -> None:
    versions = [
        ("V0", "Baseline", "Manual feature engineering + logistic regression",
         "TF-IDF + LR", "F1 0.6260", "experimental"),
        ("V1", "Sparse Classifier", "Improved text preprocessing + grid search",
         "TF-IDF + LR + GridSearch", "F1 0.6260", "experimental"),
        ("V2", "Classical Challengers", "XGBoost + FastText baselines vs LR",
         "XGBoost + FastText + LR", "F1 0.62–0.64", "experimental"),
        ("V2-R", "Learning to Rank", "Pointwise LTR with feature engineering",
         "LTR (pointwise)", "Implemented", "available"),
        ("V2.1", "Robust Evaluation", "Bootstrapped CI + ablation + recommendation",
         "Evaluation framework", "Formal evaluation", "verified"),
        ("V3", "Neural Reranker", "Cross-encoder reranking with mMARCO MiniLM",
         "Cross-encoder L12", "NDCG@10 0.6191", "verified"),
    ]

    html = '<div class="evol-container"><h3>Neural Pathway — Version Evolution</h3><div class="evol-pathway">'
    for i, (ver, name, desc, tech, metric, status) in enumerate(versions):
        if i > 0:
            html += '<div class="evol-connector"><div class="evol-connector-line"></div></div>'
        dot_cls = f"evol-node-dot-{status}"
        badge_cls = f"evol-node-badge-{status}"
        html += f"""
        <div class="evol-node">
          <div class="evol-node-dot {dot_cls}"></div>
          <div class="evol-node-body">
            <div class="evol-node-label">{ver}</div>
            <div class="evol-node-name">{name}</div>
            <div class="evol-node-badge {badge_cls}">{status}</div>
            <div style="font-size:0.65rem;color:var(--muted);margin-top:0.3rem;">{metric}</div>
          </div>
        </div>"""
    html += '</div></div>'

    st.markdown(html, unsafe_allow_html=True)

    with st.expander(t("si_evol_details"), expanded=False):
        for ver, name, desc, tech, metric, status in versions:
            st.markdown(f"""
            <div class="evol-detail-item">
              <div class="evol-detail-version">{ver}</div>
              <div class="evol-detail-body">
                <div class="evol-detail-name">{name} <span class="evol-node-badge evol-node-badge-{status}">{status}</span></div>
                <div class="evol-detail-desc">{desc}</div>
                <div class="evol-detail-tech">Technology: {tech} · Metric: {metric}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)


def render() -> None:
    hero_panel(
        title=t("search_intelligence_title"),
        subtitle=t("search_intelligence_subtitle"),
        kicker=t("search_intelligence_kicker"),
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        t("si_tab_run"), t("si_tab_baseline"),
        t("si_tab_golden"), t("si_tab_evolution"), t("si_tab_about"),
    ])

    with tab1:
        top_k = st.selectbox(t("si_top_k"), [5, 10, 20], index=1)
        if st.button(t("si_run_btn"), type="primary"):
            with st.spinner("Running evaluation against golden queries..."):
                try:
                    result = _run_evaluation(top_k=top_k)
                    st.session_state["eval_result"] = result
                    st.success(t("si_eval_complete", count=result["total_queries"]))
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

        result = st.session_state.get("eval_result")
        if result:
            current_schema = _schema_version(result)
            query_count = result.get("total_queries", 0)
            section_heading(t("si_eval_results"))
            metrics = result.get("metrics", {})

            gates_config_raw = {}
            try:
                from evaluation.search.dataset import load_quality_gates
                gates_config_raw = load_quality_gates(QUALITY_GATES_PATH)
            except Exception:
                pass
            raw_gates = gates_config_raw.get("gates", [])

            _render_search_health_header(
                _normalize_metrics(metrics, current_schema), raw_gates
            )
            _render_metrics_panel(metrics, current_schema, raw_gates)

            st.divider()
            st.markdown(f"""
            <div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem;">
              <div class="status-strip-item">
                <span class="status-strip-label">Current Evaluation</span>
                <span class="status-strip-value">{query_count} queries</span>
                <span class="status-strip-sub">Schema v{current_schema} · {result.get('timestamp','N/A')[:10]}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            _render_gates_panel(metrics, current_schema,
                                f"Current Evaluation v{current_schema}", query_count)

            if st.button(t("si_freeze_btn")):
                BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
                BASELINE_PATH.write_text(json.dumps(result, indent=2, default=str))
                st.success(t("si_frozen", path=str(BASELINE_PATH)))

            _render_query_breakdown(result.get("per_query", {}))

            raw = result.get("raw_results", {})
            if raw:
                section_heading(t("si_raw_results"))
                sample_query = next(iter(raw))
                st.json(raw[sample_query][:5])
                st.caption(f"Showing first query '{sample_query}' results")

    with tab2:
        _render_baseline_comparison()

    with tab3:
        from evaluation.search.dataset import load_golden_queries
        try:
            queries = load_golden_queries(GOLDEN_PATH)
            rows = []
            for gq in queries:
                rows.append({
                    "Query": gq.query,
                    "Intent": gq.query_intent,
                    "Expected": len(gq.expected_resource_ids),
                    "Languages": ", ".join(gq.languages),
                    "Categories": ", ".join(gq.categories),
                    "Must Include": len(gq.must_include),
                })
            st.metric(t("si_total_golden"), len(queries))
            render_safe_table(pd.DataFrame(rows), max_rows=50)

            with st.expander("Dataset Details"):
                st.code(GOLDEN_PATH.read_text(encoding="utf-8")[:3000])
        except Exception as e:
            st.warning(f"Could not load golden queries: {e}")

    with tab4:
        _render_version_evolution()

    with tab5:
        si_about = f"""
        ### {t("search_intelligence_title")}
        {t("search_intelligence_subtitle")}
        **Key Components:**
        - 67 golden queries spanning Turkish, English, and mixed-language
        - 7 core metrics: NDCG@K, MRR, MAP@K, Precision@K, Recall@K, Relevant Query Coverage, Must-Include Rate
        - 7 quality gates with pass/fail/missing status
        - Baseline comparison with schema versioning
        - Neural pathway version evolution

        **Quality Gates:**
        - NDCG@10 >= 0.100
        - MRR >= 0.150
        - Relevant Query Coverage >= 0.200
        - Result Query Coverage >= 0.800
        - Must-Include Success Rate >= 0.500
        - Precision@10 >= 0.020
        - Recall@10 >= 0.100
        """
        st.markdown(si_about)

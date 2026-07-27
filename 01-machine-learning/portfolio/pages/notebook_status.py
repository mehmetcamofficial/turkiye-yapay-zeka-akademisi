from __future__ import annotations
from html import escape

import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from portfolio.config import (
    ARTIFACTS_DIR,
    DATA_SCIENCE_MIDTERM_DIR,
    GITHUB_BRANCH,
    GITHUB_OWNER,
    GITHUB_REPO,
    ML_ROOT,
    REPOSITORY_ROOT,
    TRENDYOL_PROFILE_DIR,
)
from portfolio.data_science_registry import evaluate_midterm
from portfolio.experiment_store import EXPERIMENT_TYPES, load_experiments, normalize_gridsearch_results
from portfolio.i18n import t
from portfolio.ui_components import (
    empty_state,
    hero_panel,
    information_panel,
    kpi_grid,
    render_safe_table,
    section_heading,
)

CANONICAL_FILES = [
    "cardinality_summary.csv", "categorical_summary.csv", "column_profile.csv",
    "data_quality_report.json", "data_type_summary.csv", "duplicate_summary.csv",
    "missing_values.csv", "numeric_summary.csv", "profile_summary.md",
    "schema_report.json", "table_summary.csv", "text_length_summary.csv",
]


def _repo_rel_path(path: str | Path | None) -> str:
    if path is None:
        return "\u2014"
    try:
        p = Path(path).resolve()
        return str(p.relative_to(REPOSITORY_ROOT))
    except (ValueError, OSError):
        try:
            p = Path(path)
            return str(p.relative_to(REPOSITORY_ROOT))
        except (ValueError, OSError):
            return Path(path).name


def _discover_notebooks() -> list[dict]:
    notebooks: list[dict] = []
    for path in sorted(REPOSITORY_ROOT.rglob("*.ipynb")):
        if ".ipynb" not in path.name:
            continue
        if ".git" in str(path):
            continue
        if "venv" in str(path) or ".venv" in str(path) or "__pycache__" in str(path):
            continue
        if "site-packages" in str(path):
            continue
        rel = _repo_rel_path(path)
        nb_name = path.name
        nb_data = path.read_bytes() if path.is_file() else b""

        github_url = (
            f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
            f"/blob/{GITHUB_BRANCH}/{rel}"
        )
        colab_url = (
            f"https://colab.research.google.com/github/"
            f"{GITHUB_OWNER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{rel}"
        )

        has_outputs = False
        has_metadata = True
        try:
            nb_json = json.loads(nb_data)
            for cell in nb_json.get("cells", []):
                if cell.get("cell_type") == "code" and cell.get("outputs"):
                    has_outputs = True
                    break
            meta = nb_json.get("metadata", {})
            if not meta or not any(k for k in meta if k not in ("kernelspec", "language_info")):
                has_metadata = False
        except (json.JSONDecodeError, ValueError):
            has_outputs = False
            has_metadata = False

        notebooks.append({
            "path": rel,
            "name": nb_name,
            "raw_path": str(path),
            "github_url": github_url,
            "colab_url": colab_url,
            "colab_valid": True,
            "has_outputs": has_outputs,
            "has_metadata": has_metadata,
            "size_bytes": len(nb_data),
            "bytes": nb_data,
        })
    return notebooks


def _profile_outputs_count() -> int:
    outputs_dir = TRENDYOL_PROFILE_DIR / "outputs"
    if not outputs_dir.is_dir():
        return 0
    return sum(1 for f in CANONICAL_FILES if (outputs_dir / f).is_file())


def _render_notebook_tab(midterm: dict) -> None:
    notebooks = _discover_notebooks()
    section_heading(t("notebook_execution_status"))
    info_lines = [_repo_rel_path(n["path"]) for n in notebooks]
    if info_lines:
        st.caption(f"{len(notebooks)} notebook(s) discovered")
        for line in info_lines:
            st.text(line)
    else:
        st.caption("No notebooks discovered")

    for idx, nb in enumerate(notebooks):
        with st.container():
            st.markdown(
                f'<div class="card" style="padding:1rem;margin-bottom:0.75rem;">'
                f"<strong>{escape(nb['name'])}</strong><br>"
                f'<span style="font-size:0.8rem;color:var(--muted);">{escape(nb["path"])}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.link_button(
                    t("notebook_colab"),
                    nb["colab_url"],
                    type="secondary",
                    use_container_width=True,
                )
            with col_b:
                st.link_button(
                    t("view_on_github"),
                    nb["github_url"],
                    type="secondary",
                    use_container_width=True,
                )
            with col_c:
                st.download_button(
                    t("download_ipynb"),
                    nb["bytes"],
                    nb["name"],
                    "application/x-ipynb+json",
                    use_container_width=True,
                )

    if midterm["notebook_ready"]:
        information_panel(t("notebook_exec_status"), t("notebook_executed_yes"))
    else:
        information_panel(t("notebook_exec_status"), t("notebook_executed_no"))

    section_heading(t("metadata_schema_compat"))
    compatible = midterm.get("schema_compatible", False)
    available = midterm.get("available_columns", [])
    required = midterm.get("required_columns", [])
    status_text = t("compatible") if compatible else t("partial_compatibility")
    information_panel(
        t("schema_compatibility"),
        f"{status_text} \u2014 {len(available)}/{len(required)} {t('schema_fields')}",
    )


def _render_experiments_tab() -> None:
    section_heading(t("experiments_title"))
    experiments = load_experiments()
    if not experiments:
        st.markdown(
            f'<div class="empty-state" style="text-align:left;padding:1.25rem;">'
            f"<strong>{escape(t('experiments_empty'))}</strong>"
            f"<p>{escape(t('experiments_empty_desc'))}</p>"
            f'<div style="margin-top:0.75rem;display:flex;flex-wrap:wrap;gap:0.4rem;">'
            f'<span class="badge badge-available">{escape(t("experiments_empty_training"))}</span>'
            f'<span class="badge badge-available">{escape(t("experiments_empty_search"))}</span>'
            f'<span class="badge badge-available">{escape(t("experiments_empty_placeholder"))}</span>'
            f"</div></div>",
            unsafe_allow_html=True,
        )
        return

    exp_sorted = sorted(experiments, key=lambda e: e.get("started_at", ""), reverse=True)
    total = len(exp_sorted)
    completed = sum(1 for e in exp_sorted if e.get("status") == "completed")
    failed = sum(1 for e in exp_sorted if e.get("status") == "failed")
    latest = exp_sorted[0].get("started_at", "")[:19] if exp_sorted else ""

    kpi_grid([
        (t("exp_total"), str(total), ""),
        (t("exp_completed"), str(completed), ""),
        (t("exp_failed"), str(failed), ""),
        (t("exp_latest_run"), latest[:10] if latest else "\u2014", ""),
    ])

    capabilities = sorted({e.get("capability", "") for e in exp_sorted})
    exp_types = sorted({e.get("experiment_type", "") for e in exp_sorted})
    statuses = sorted({e.get("status", "") for e in exp_sorted})

    filter_cols = st.columns(3)
    with filter_cols[0]:
        cap_filter = st.selectbox(t("exp_capability_filter"), [t("exp_filter_all")] + capabilities)
    with filter_cols[1]:
        type_filter = st.selectbox(t("exp_type_filter"), [t("exp_filter_all")] + [t(f"exp_{et}") for et in exp_types])
    with filter_cols[2]:
        status_filter = st.selectbox(t("exp_status_filter"), [t("exp_filter_all")] + statuses)

    filtered = exp_sorted
    if cap_filter != t("exp_filter_all"):
        filtered = [e for e in filtered if e.get("capability") == cap_filter]
    if type_filter != t("exp_filter_all"):
        reverse_type_map = {t(f"exp_{et}"): et for et in EXPERIMENT_TYPES}
        mapped_type = reverse_type_map.get(type_filter, type_filter)
        filtered = [e for e in filtered if e.get("experiment_type") == mapped_type]
    if status_filter != t("exp_filter_all"):
        filtered = [e for e in filtered if e.get("status") == status_filter]

    if not filtered:
        empty_state(t("experiments_empty"))
        return

    _type_label = {
        "training": t("exp_training"),
        "evaluation": t("exp_evaluation"),
        "hyperparameter_search": t("exp_hyperparameter_search"),
        "benchmark": t("exp_benchmark"),
    }

    rows = []
    for e in filtered:
        dur = e.get("duration_ms", 0)
        dur_str = f"{dur}{t('exp_duration_ms')}" if dur else "\u2014"
        metrics = e.get("metrics", {}) or {}
        primary = next(iter(metrics.values())) if metrics else "\u2014"
        if isinstance(primary, float):
            primary = f"{primary:.4f}"
        elif not isinstance(primary, str):
            primary = str(primary)
        rows.append({
            t("exp_name_col"): e.get("model_name", e.get("experiment_id", "")),
            t("exp_capability_col"): e.get("capability", ""),
            t("exp_type_col"): _type_label.get(e.get("experiment_type", ""), e.get("experiment_type", "")),
            t("exp_model_col"): e.get("model_name", ""),
            t("exp_status_col"): e.get("status", ""),
            t("exp_started_col"): str(e.get("started_at", ""))[:19],
            t("exp_duration_col"): dur_str,
            t("exp_metric_col"): str(primary),
        })

    render_safe_table(rows, max_rows=200)

    st.divider()
    section_heading(t("exp_details"))
    selected_eid = st.session_state.get("selected_experiment_id")
    for e in filtered:
        is_selected = bool(selected_eid and e.get("experiment_id") == selected_eid)
        with st.expander(
            f"{e.get('model_name', e.get('experiment_id', ''))} — {e.get('status', '')}",
            expanded=is_selected,
        ):
            if is_selected:
                st.success(t("exp_details"))
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{t('exp_metrics')}**")
                metrics = e.get("metrics", {}) or {}
                if metrics:
                    for k, v in metrics.items():
                        st.text(f"{k}: {v}")
                else:
                    st.text("\u2014")
                st.markdown(f"**{t('exp_parameters')}**")
                params = e.get("parameters", {}) or {}
                if params:
                    for k, v in params.items():
                        st.text(f"{k}: {v}")
                else:
                    st.text("\u2014")
            with c2:
                st.markdown(f"**{t('exp_artifacts')}**")
                art = e.get("artifact_paths", []) or []
                if art:
                    for a in art:
                        st.text(a)
                else:
                    st.text("\u2014")
                st.markdown(f"**{t('exp_source')}**")
                st.text(e.get("source", "\u2014"))
                st.markdown(f"**{t('exp_notes')}**")
                st.text(e.get("notes", "\u2014"))
                st.markdown(f"**{t('exp_timestamps')}**")
                st.text(f"{t('exp_started_at')}: {str(e.get('started_at', ''))[:19]}")
                st.text(f"{t('exp_completed_at')}: {str(e.get('completed_at', ''))[:19]}")

    st.divider()
    section_heading(t("exp_compare"))
    selected = []
    for e in filtered:
        key = f"exp_cmp_{e['experiment_id']}"
        checked = st.checkbox(e.get("model_name", e["experiment_id"]), key=key)
        if checked:
            selected.append(e)
    if len(selected) >= 2:
        section_heading(t("exp_compare_title"))
        cmp_rows = []
        for e in selected:
            metrics = e.get("metrics", {}) or {}
            primary = next(iter(metrics.values())) if metrics else "\u2014"
            if isinstance(primary, float):
                primary = f"{primary:.4f}"
            cmp_rows.append({
                t("exp_name_col"): e.get("model_name", e["experiment_id"]),
                t("exp_model_col"): e.get("model_name", ""),
                t("exp_metric_col"): str(primary),
                t("exp_duration_col"): f"{e.get('duration_ms', 0)}{t('exp_duration_ms')}",
                t("exp_parameters"): str(e.get("parameters", {})),
            })
        render_safe_table(cmp_rows)
    elif selected:
        st.caption(t("exp_no_selection"))


def _render_artifacts_tab() -> None:
    section_heading(t("artifacts_section"))
    outputs_dir = TRENDYOL_PROFILE_DIR / "outputs"
    profile_count = _profile_outputs_count()

    st.caption(f"{t('artifacts_count')}: {profile_count}/{len(CANONICAL_FILES)}")

    if profile_count > 0 and outputs_dir.is_dir():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for fname in CANONICAL_FILES:
                fpath = outputs_dir / fname
                if fpath.is_file():
                    zf.write(str(fpath), fname)
        buf.seek(0)
        st.download_button(
            t("artifacts_bundle_download"),
            buf,
            "canonical_outputs.zip",
            "application/zip",
        )

    rows = [
        {
            t("artifacts_filename"): fname,
            t("table_status"): t("manifest_present") if (outputs_dir / fname).is_file() else t("manifest_missing"),
        }
        for fname in CANONICAL_FILES
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_metadata_tab(midterm: dict) -> None:
    section_heading(t("metadata_dataset_info"))
    ds_path = midterm.get("dataset_path")
    information_panel(
        t("local_dataset"),
        _repo_rel_path(ds_path) if ds_path else t("status_unavailable"),
    )

    required = midterm.get("required_columns", [])
    available = midterm.get("available_columns", [])
    missing = midterm.get("missing_columns", [])

    section_heading(t("metadata_columns_info"))
    col1, col2, col3 = st.columns(3)
    with col1:
        information_panel(t("metadata_required_cols"), str(len(required)))
    with col2:
        information_panel(t("metadata_available_cols"), str(len(available)))
    with col3:
        information_panel(t("metadata_missing_cols"), str(len(missing)))

    if missing:
        st.markdown("**" + t("metadata_missing_cols") + "**")
        st.code(", ".join(missing))

    section_heading(t("metadata_schema_compat"))
    compatible = midterm.get("schema_compatible", False)
    status_text = t("compatible") if compatible else t("partial_compatibility")
    st.caption(f"{status_text} \u2014 {len(available)}/{len(required)} {t('schema_fields')}")

    inventory = midterm.get("inventory", [])
    if inventory:
        section_heading(t("metadata_dataset_rows"))
        for rec in inventory:
            row_path = rec.get("relative_path", "?")
            row_count = rec.get("row_count", "?")
            st.text(f"{row_path}: {row_count} {t('metadata_available_rows')}")


def render() -> None:
    midterm = evaluate_midterm()
    profile_count = _profile_outputs_count()
    notebooks = _discover_notebooks()

    hero_panel(
        title=t("nav_notebook_status"),
        subtitle=t("subtitle_notebook_status"),
        kicker=t("section_portfolio"),
    )

    nb_count = len(notebooks)
    gh_count = nb_count
    colab_count = nb_count
    dl_count = nb_count
    with_outputs = sum(1 for n in notebooks if n.get("has_outputs"))
    with_metadata = sum(1 for n in notebooks if n.get("has_metadata"))

    kpi_grid([
        (t("local_dataset"), t("status_available") if midterm["dataset_path"] else t("status_unavailable"),
         f"{midterm['downloaded_file_count']} {t('files_locally')}"),
        (t("notebook_label"), str(nb_count),
         f"{gh_count} {t('github')} / {colab_count} {t('colab')} / {dl_count} {t('download')}"),
        (t("profile_outputs"), f"{profile_count}/{len(CANONICAL_FILES)}",
         t("profile_outputs_available")),
        (t("schema_compatibility"), t("compatible") if midterm["schema_compatible"] else t("partial_compatibility"),
         f"{len(midterm['available_columns'])}/{len(midterm['required_columns'])} {t('schema_fields')}"),
    ])

    # Deep-link from Search Workspace may request the experiments tab.
    requested_tab = st.session_state.pop("notebook_status_tab", None)
    tab_labels = [t("tab_notebook"), t("tab_experiments"), t("tab_artifacts"), t("tab_metadata")]
    tabs = st.tabs(tab_labels)
    if requested_tab == "experiments":
        st.caption(t("exp_registry_title"))

    with tabs[0]:
        _render_notebook_tab(midterm)

    with tabs[1]:
        _render_experiments_tab()

    with tabs[2]:
        _render_artifacts_tab()

    with tabs[3]:
        _render_metadata_tab(midterm)

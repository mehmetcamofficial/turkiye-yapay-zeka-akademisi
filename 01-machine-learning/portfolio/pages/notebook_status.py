"""Notebook & Experiment Library page."""

# i18n keys needed: tab_notebook, tab_experiments, tab_artifacts, tab_metadata
# experiment_name, experiment_path, experiment_items, experiment_modified
# notebook_execution_status, notebook_download, notebook_colab
# artifacts_section, artifacts_count, artifacts_bundle_download
# metadata_dataset_info, metadata_columns_info, metadata_required_cols
# metadata_available_cols, metadata_missing_cols, metadata_dataset_rows
# metadata_available_rows, experiments_title, experiments_empty
# experiments_empty_desc, experiment_type, experiment_size

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from portfolio.config import DATA_SCIENCE_MIDTERM_DIR, ML_ROOT, TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.ui_components import (
    empty_state,
    hero_panel,
    information_panel,
    kpi_grid,
    section_heading,
)

CANONICAL_FILES = [
    "cardinality_summary.csv", "categorical_summary.csv", "column_profile.csv",
    "data_quality_report.json", "data_type_summary.csv", "duplicate_summary.csv",
    "missing_values.csv", "numeric_summary.csv", "profile_summary.md",
    "schema_report.json", "table_summary.csv", "text_length_summary.csv",
]

EXPERIMENTS_ROOT = Path(ML_ROOT) / "05-data-science-files" / "SAKARYA_UYGULAMA"


def _rel_path(path: str | None) -> str:
    if path is None:
        return "\u2014"
    try:
        p = Path(path)
        repo_root = Path(__file__).resolve().parents[3]
        return str(p.relative_to(repo_root))
    except (ValueError, TypeError):
        return str(path)


def _profile_outputs_count() -> int:
    outputs_dir = TRENDYOL_PROFILE_DIR / "outputs"
    if not outputs_dir.is_dir():
        return 0
    return sum(1 for f in CANONICAL_FILES if (outputs_dir / f).is_file())


def _experiments_list() -> list[dict[str, str]]:
    if not EXPERIMENTS_ROOT.is_dir():
        return []
    results: list[dict[str, str]] = []
    for child in sorted(EXPERIMENTS_ROOT.iterdir()):
        modified = datetime.fromtimestamp(child.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        if child.is_dir():
            items = sum(1 for _ in child.iterdir())
            ftype = "directory"
        else:
            items = 1
            ftype = child.suffix.lstrip(".").upper() if child.suffix else "file"
        size_kb = child.stat().st_size / 1024
        results.append({
            "experiment_name": child.name,
            "experiment_type": ftype,
            "experiment_items": str(items),
            "experiment_size": f"{size_kb:.1f} KB",
            "experiment_modified": modified,
        })
    return results


def _render_notebook_tab(midterm: dict) -> None:
    section_heading(t("notebook_execution_status"))
    if midterm["notebook_ready"]:
        information_panel(t("notebook_exec_status"), t("notebook_executed_yes"))
    else:
        information_panel(t("notebook_exec_status"), t("notebook_executed_no"))

    nb_path = midterm.get("notebook_path")
    if nb_path:
        resolved = Path(nb_path)
        if resolved.is_file():
            section_heading(t("notebook_download"))
            with open(resolved, "rb") as f:
                st.download_button(
                    t("download_ipynb"),
                    f.read(),
                    resolved.name,
                    "application/x-ipynb+json",
                )

    section_heading(t("notebook_colab"))
    colab_url = midterm.get("colab_url", "")
    if colab_url and "github.com" in colab_url.lower():
        st.link_button(t("open_in_colab"), colab_url)
    else:
        st.info(t("colab_not_configured"))

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
    experiments = _experiments_list()
    if not experiments:
        empty_state(t("experiments_empty"), t("experiments_empty_desc"))
        return

    rows = [
        {
            t("experiment_name"): e["experiment_name"],
            t("experiment_type"): e["experiment_type"],
            t("experiment_items"): e["experiment_items"],
            t("experiment_size"): e["experiment_size"],
            t("experiment_modified"): e["experiment_modified"],
        }
        for e in experiments
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


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
        _rel_path(ds_path) if ds_path else t("status_unavailable"),
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

    hero_panel(
        title=t("nav_notebook_status"),
        subtitle=t("subtitle_notebook_status"),
        kicker=t("section_portfolio"),
    )

    kpi_grid([
        (t("local_dataset"), t("status_available") if midterm["dataset_path"] else t("status_unavailable"),
         f"{midterm['downloaded_file_count']} {t('files_locally')}"),
        (t("notebook_label"), t("status_available") if midterm["notebook_ready"] else t("status_unavailable"),
         _rel_path(midterm["notebook_path"])),
        (t("profile_outputs"), f"{profile_count}/{len(CANONICAL_FILES)}",
         t("profile_outputs_available")),
        (t("schema_compatibility"), t("compatible") if midterm["schema_compatible"] else t("partial_compatibility"),
         f"{len(midterm['available_columns'])}/{len(midterm['required_columns'])} {t('schema_fields')}"),
    ])

    tabs = st.tabs([t("tab_notebook"), t("tab_experiments"), t("tab_artifacts"), t("tab_metadata")])

    with tabs[0]:
        _render_notebook_tab(midterm)

    with tabs[1]:
        _render_experiments_tab()

    with tabs[2]:
        _render_artifacts_tab()

    with tabs[3]:
        _render_metadata_tab(midterm)

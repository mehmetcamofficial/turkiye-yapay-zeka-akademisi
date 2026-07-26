from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from portfolio.config import DATA_SCIENCE_MIDTERM_DIR, TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe, load_text_safe
# i18n keys needed: gib_unit, category_profile_not_found, brand_profile_not_found, label_distribution_not_found

from portfolio.ui_components import (empty_state, hero_panel, information_panel,
                                     kpi_grid, metric_table, status_badge)

CANONICAL_FILES = [
    "cardinality_summary.csv", "categorical_summary.csv", "column_profile.csv",
    "data_quality_report.json", "data_type_summary.csv", "duplicate_summary.csv",
    "missing_values.csv", "numeric_summary.csv", "profile_summary.md",
    "schema_report.json", "table_summary.csv", "text_length_summary.csv",
]


def _profile_outputs_count() -> int:
    outputs_dir = TRENDYOL_PROFILE_DIR / "outputs"
    if not outputs_dir.is_dir():
        return 0
    return sum(1 for f in CANONICAL_FILES if (outputs_dir / f).is_file())


def _filter(frame: pd.DataFrame, **criteria: str) -> pd.DataFrame:
    result = frame.copy()
    for column, value in criteria.items():
        if column in result:
            result = result[result[column].astype(str) == value]
    return result


def render() -> None:
    item = evaluate_midterm()
    outputs = TRENDYOL_PROFILE_DIR / "outputs"
    profile_count = _profile_outputs_count()

    hero_panel(
        title=t("dataset_overview_title"),
        subtitle=t("dataset_overview_subtitle"),
        kicker=t("section_data_science"),
    )
    st.markdown(status_badge(item["status"]), unsafe_allow_html=True)

    status_items = [
        (t("status_label"), t("status_available") if item["inventory_ready"] else t("not_available"), None),
        (t("midterm_source_files"), str(item["downloaded_file_count"]), None),
        (t("midterm_total_size"), f"{item['downloaded_size_bytes']/1024**3:.2f} {t('gib_unit')}", None),
        (t("profile_outputs"), f"{profile_count}/{len(CANONICAL_FILES)}", None),
        (t("notebook_label"), t("ready") if item["notebook_ready"] else t("not_available"), None),
        (t("schema_compatibility"), t("partial_compatibility") if not item["schema_compatible"] else t("compatible"), None),
        (t("midterm_last_verified"), (item["last_verified"] or "—").replace("T", " "), None),
    ]
    kpi_grid(status_items)

    tabs = st.tabs([
        t("midterm_tab_overview"),
        t("midterm_tab_inventory"),
        t("tab_quality"),
        t("midterm_tab_category_brand"),
        t("midterm_tab_text"),
        t("midterm_tab_labels"),
        t("tab_outputs"),
        t("tab_schema"),
        t("tab_tech_details"),
    ])

    with tabs[0]:
        information_panel(t("purpose"), t("midterm_purpose_desc"))
        progress_pct = int(profile_count / len(CANONICAL_FILES) * 100)
        st.progress(progress_pct / 100, text=f"{t('overall_progress')}: {progress_pct}%")
        kpi_grid([
            (t("midterm_source_files"), str(item['downloaded_file_count']), None),
            (t("profile_outputs"), f"{profile_count}/{len(CANONICAL_FILES)}", None),
            (t("notebook_label"), t("ready") if item['notebook_ready'] else t("not_available"), None),
            (t("schema_compatibility"), t("compatible") if item['schema_compatible'] else t("partial_compatibility"), None),
        ])
        information_panel(t("limitations_panel"), t("limitations_desc_short"))
        information_panel(t("next_actions_panel"), t("next_actions_desc"))

    with tabs[1]:
        inventory = pd.DataFrame(item["inventory"])
        if not inventory.empty:
            inventory["size_mb"] = inventory["size_bytes"] / 1024**2
            metric_table(inventory[["relative_path", "extension", "size_mb", "row_count", "column_count", "readable"]])

    with tabs[2]:
        metric_table(load_csv_safe(str(outputs / "missing_values.csv")))
        metric_table(load_csv_safe(str(outputs / "duplicate_summary.csv")))
        metric_table(load_csv_safe(str(outputs / "cardinality_summary.csv")))

    with tabs[3]:
        categories = load_csv_safe(str(outputs / "categorical_summary.csv"))
        metric_table(_filter(categories, column="category"), t("category_profile_not_found"))
        metric_table(_filter(categories, column="brand"), t("brand_profile_not_found"))

    with tabs[4]:
        lengths = load_csv_safe(str(outputs / "text_length_summary.csv"))
        metric_table(lengths[lengths["column"].isin(["title", "query", "attributes"])] if "column" in lengths else lengths)
        information_panel(t("midterm_comment"), t("midterm_comment_desc"))

    with tabs[5]:
        labels = load_csv_safe(str(outputs / "categorical_summary.csv"))
        metric_table(_filter(labels, column="label"), t("label_distribution_not_found"))

    with tabs[6]:
        files_data = [
            {t("midterm_output_label"): name, t("table_status"): t("manifest_present")}
            for name in item["profile_outputs"]
        ]
        metric_table(pd.DataFrame(files_data))

    with tabs[7]:
        schema = load_json_safe(str(outputs / "schema_report.json"))
        if schema and schema.get("required_fields"):
            match_type_map = {
                "Direct Match": t("match_direct"),
                "Safe Semantic Match": t("match_semantic"),
                "Semantic Match": t("match_semantic"),
                "Missing": t("match_unavailable"),
                "Unavailable": t("match_unavailable"),
                "Requires Enrichment": t("match_enrichment"),
            }
            for field in schema["required_fields"]:
                raw_type = field.get("match_type", "")
                field["match_type"] = match_type_map.get(raw_type, raw_type)
            metric_table(schema["required_fields"])
            st.caption(t("schema_fields_explanation"))
        with st.expander(t("midterm_schema_compat_note"), expanded=False):
            st.markdown(load_text_safe(str(DATA_SCIENCE_MIDTERM_DIR / "SCHEMA_COMPATIBILITY.md")))
            st.info(t("midterm_schema_compat_desc"))

    with tabs[8]:
        with st.expander(t("midterm_profile_scope"), expanded=False):
            st.markdown(load_text_safe(str(outputs / "profile_summary.md")))
            st.markdown(load_text_safe(str(DATA_SCIENCE_MIDTERM_DIR / "DATA_SOURCE.md")))
        notebook = item["notebook_path"]
        if notebook and Path(notebook).is_file():
            st.download_button(t("midterm_download_notebook"), Path(notebook).read_bytes(), Path(notebook).name, "application/x-ipynb+json")

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from portfolio.config import TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.loaders import load_json_safe
from portfolio.ui_components import (empty_state, hero_panel, kpi_grid,
                                     render_safe_table, section_heading)

PROFILE_DIR = TRENDYOL_PROFILE_DIR


def _load_schema() -> dict[str, Any] | None:
    path = PROFILE_DIR / "outputs" / "schema_report.json"
    if path.is_file():
        return load_json_safe(str(path))
    return None


def _load_quality() -> list[dict[str, Any]]:
    path = PROFILE_DIR / "outputs" / "data_quality_report.json"
    if path.is_file():
        data = load_json_safe(str(path))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "tables" in data:
            return data["tables"]
    return []


def _profile_outputs() -> list[str]:
    return sorted(
        path.name for path in (PROFILE_DIR / "outputs").glob("*")
        if path.is_file() and path.name != ".gitkeep"
    )


def render() -> None:
    hero_panel(
        title=t("nav_data_workspace"),
        subtitle=t("subtitle_data_science_overview"),
        kicker=t("section_data_science"),
    )

    midterm = evaluate_midterm()

    tabs = st.tabs([
        t("nav_overview"),
        "Inventory",
        "Schema",
        "Data Quality",
        "Outputs",
    ])

    with tabs[0]:
        schema_report = _load_schema()
        required_fields = schema_report.get("required_fields", []) if schema_report else []
        available_cols = len(required_fields)
        kpi_grid([
            ("Status", "Available", "Technical completion verified"),
            ("Local Dataset", "Available" if midterm["dataset_path"] else "Cloud excluded",
             f"{midterm['downloaded_file_count']} files locally"),
            ("Schema Fields", str(available_cols),
             "From persisted profile" if available_cols else "Not available"),
            ("Notebook", "Ready" if midterm["notebook_ready"] else "Not Available",
             "Verified locally"),
            ("Profile Outputs", str(len(_profile_outputs())),
             "Generated from trendyol-profile"),
        ])

    with tabs[1]:
        inventory = midterm.get("inventory")
        if isinstance(inventory, list) and inventory:
            section_heading("Dataset Inventory", "Downloaded Trendyol dataset files")
            inv_rows = [
                {"File": r.get("relative_path", r.get("file", "—")),
                 "Size (MB)": f"{r.get('size_bytes', 0) / 1024 / 1024:.2f}"}
                for r in inventory
            ]
            render_safe_table(inv_rows, download_name="dataset_inventory.csv")
        else:
            empty_state("Dataset Inventory",
                        "Raw dataset inventory is only available when run locally. "
                        "Profile outputs remain available.")

    with tabs[2]:
        schema = _load_schema()
        if schema and schema.get("required_fields"):
            section_heading("Schema Report", "Column-level schema analysis from persisted profile")
            render_safe_table(
                schema["required_fields"],
                column_map={"required_field": "Required Field", "source_file": "Source File",
                            "actual_field": "Actual Field", "match_type": "Match Type",
                            "transformation": "Transformation", "confidence": "Confidence"},
                download_name="schema_report.csv",
            )
        else:
            empty_state("Schema Report",
                        "Schema report generated from persisted trendyol-profile outputs.")

    with tabs[3]:
        quality = _load_quality()
        if quality:
            section_heading("Data Quality", "Quality metrics from persisted profile")
            render_safe_table(quality, download_name="data_quality.csv")
        else:
            empty_state("Quality Report",
                        "Data quality report generated from persisted trendyol-profile outputs.")

    with tabs[4]:
        outputs = _profile_outputs()
        if outputs:
            section_heading("Profile Outputs", f"{len(outputs)} generated files")
            st.markdown("\n".join(f"- `{o}`" for o in outputs))
        else:
            empty_state("Profile Outputs", "Not available.")

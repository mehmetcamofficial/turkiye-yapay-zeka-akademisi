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
        t("tab_inventory"),
        t("tab_schema"),
        t("tab_quality"),
        t("tab_outputs"),
    ])

    with tabs[0]:
        schema_report = _load_schema()
        required_fields = schema_report.get("required_fields", []) if schema_report else []
        available_cols = len(required_fields)
        kpi_grid([
            (t("status_label"), t("status_available"), t("technical_completion_verified")),
            (t("local_dataset"), t("status_available") if midterm["dataset_path"] else t("cloud_excluded"),
             f"{midterm['downloaded_file_count']} {t('files_locally')}"),
            (t("schema_fields"), str(available_cols),
             t("from_persisted_profile") if available_cols else t("not_available")),
            (t("notebook_label"), t("ready") if midterm["notebook_ready"] else t("not_available"),
             t("verified_locally")),
            (t("profile_outputs"), str(len(_profile_outputs())),
             t("generated_from_trendyol_profile")),
        ])

    with tabs[1]:
        inventory = midterm.get("inventory")
        if isinstance(inventory, list) and inventory:
            section_heading(t("dataset_inventory"), t("downloaded_trendyol_files"))
            inv_rows = [
                {"File": r.get("relative_path", r.get("file", "—")),
                 t("size_mb"): f"{r.get('size_bytes', 0) / 1024 / 1024:.2f}"}
                for r in inventory
            ]
            render_safe_table(inv_rows, download_name="dataset_inventory.csv")
        else:
            empty_state(t("dataset_inventory"),
                        t("inventory_local_only"))

    with tabs[2]:
        schema = _load_schema()
        if schema and schema.get("required_fields"):
            section_heading(t("schema_report"), t("schema_report_desc"))
            render_safe_table(
                schema["required_fields"],
                column_map={"required_field": t("required_field"), "source_file": t("source_file"),
                            "actual_field": t("actual_field"), "match_type": t("match_type"),
                            "transformation": t("transformation"), "confidence": t("confidence")},
                download_name="schema_report.csv",
            )
        else:
            empty_state(t("schema_report"),
                        t("schema_report_generated"))

    with tabs[3]:
        quality = _load_quality()
        if quality:
            section_heading(t("data_quality"), t("quality_metrics_from_profile"))
            render_safe_table(quality, download_name="data_quality.csv")
        else:
            empty_state(t("quality_report"),
                        t("quality_report_generated"))

    with tabs[4]:
        outputs = _profile_outputs()
        if outputs:
            section_heading(t("profile_outputs"), f"{len(outputs)} {t('generated_files')}")
            st.markdown("\n".join(f"- `{o}`" for o in outputs))
        else:
            empty_state(t("profile_outputs"), t("not_available"))

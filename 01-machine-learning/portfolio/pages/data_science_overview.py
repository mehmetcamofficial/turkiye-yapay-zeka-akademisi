from __future__ import annotations

import streamlit as st

from portfolio.config import TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.loaders import load_json_safe
from portfolio.ui_components import (empty_state, hero_panel, kpi_grid,
                                     render_safe_table, section_heading,
                                     status_badge)

PROFILE_DIR = TRENDYOL_PROFILE_DIR


def render() -> None:
    hero_panel(
        title=t("nav_data_workspace"),
        subtitle="Trendyol e-commerce dataset inventory, schema, quality, and profiling.",
        kicker="DATA & QUALITY",
    )

    midterm = evaluate_midterm()

    tabs = st.tabs([
        "Overview / Genel Bakış",
        "Inventory / Envanter",
        "Schema / Şema",
        "Data Quality / Veri Kalitesi",
        "Outputs / Çıktılar",
    ])

    with tabs[0]:
        kpi_grid([
            ("Status", status_badge(midterm.get("status", "limited")),
             f"Technical: {status_badge(midterm.get('technical_status', 'limited'))}"),
            ("Dataset", "Ready" if midterm["dataset_path"] else "Not Available",
             f"{midterm['downloaded_file_count']} files"),
            ("Columns", f"{len(midterm['available_columns'])}/{len(midterm['required_columns'])}",
             f"{len(midterm['missing_columns'])} missing" if midterm['missing_columns'] else "Complete"),
            ("Notebook", "Ready" if midterm["notebook_ready"] else "Not Available",
             "Verified locally"),
            ("Profile Outputs", str(len(midterm["profile_outputs"])),
             "Generated from trendypol-profile"),
            ("Colab", "Published" if midterm["colab_configured"] else "Not Published",
             "Separate from technical completion"),
        ])

    with tabs[1]:
        inventory = midterm.get("inventory", {})
        if isinstance(inventory, dict) and inventory:
            section_heading("Dataset Inventory", "Downloaded Trendyol dataset files")
            inv_rows = [{"File": k, "Size (MB)": f"{v.get('size_bytes', 0) / 1024 / 1024:.2f}"}
                        for k, v in inventory.items()]
            render_safe_table(inv_rows, download_name="dataset_inventory.csv")

    with tabs[2]:
        schema_report = load_json_safe(str(PROFILE_DIR / "outputs" / "schema_report.json"))
        if schema_report:
            section_heading("Schema Report", "Column-level schema analysis")
            render_safe_table(schema_report.get("columns", []),
                              column_map={"name": "Column", "dtype": "Type", "missing": "Missing",
                                          "unique": "Unique"},
                              download_name="schema_report.csv")
        else:
            empty_state("Schema Report", "Not available locally.")

    with tabs[3]:
        quality_report = load_json_safe(str(PROFILE_DIR / "outputs" / "data_quality_report.json"))
        if quality_report:
            section_heading("Data Quality", "Quality metrics")
            render_safe_table(quality_report.get("tables", []), download_name="data_quality.csv")
        else:
            empty_state("Quality Report", "Not available locally.")

    with tabs[4]:
        outputs = sorted(
            path.name for path in (PROFILE_DIR / "outputs").glob("*")
            if path.is_file() and path.name != ".gitkeep"
        )
        if outputs:
            section_heading("Profile Outputs", f"{len(outputs)} generated files")
            st.markdown("\n".join(f"- `{o}`" for o in outputs))
        else:
            empty_state("Profile Outputs", "Not available.")

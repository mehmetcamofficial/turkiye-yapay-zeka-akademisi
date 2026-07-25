from __future__ import annotations

import streamlit as st

from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.ui_components import hero_panel, kpi_grid


def render() -> None:
    hero_panel(
        title=t("nav_notebook_status"),
        subtitle=t("subtitle_notebook_status"),
        kicker=t("nav_academic"),
    )

    midterm = evaluate_midterm()

    kpi_grid([
        ("Dataset", "Ready" if midterm["dataset_path"] else "Not Available",
         f"{midterm['downloaded_file_count']} files, {midterm['downloaded_size_bytes'] / (1024**3):.2f} GiB"),
        ("Notebook", "Ready" if midterm["notebook_ready"] else "Not Available",
         str(midterm["notebook_path"])),
        ("Outputs", f"{len(midterm['existing_outputs'])}/{len(midterm['expected_outputs'])}",
         f"{len(midterm['profile_outputs'])} profile outputs"),
        ("Schema", "Compatible" if midterm["schema_compatible"] else "Issues",
         f"{len(midterm['available_columns'])}/{len(midterm['required_columns'])} columns"),
        ("Questions", f"{midterm['completed_questions']}/{midterm['total_questions']}",
         f"{len(midterm['supported_questions'])} supported"),
        ("Colab", "Published" if midterm["colab_configured"] else "Not Published",
         "Separate from technical completion"),
    ])

    st.info(
        "Technical completion is verified independently from Colab publication. "
        "The notebook and outputs are portfolio-ready even if no public Colab URL is configured."
    )

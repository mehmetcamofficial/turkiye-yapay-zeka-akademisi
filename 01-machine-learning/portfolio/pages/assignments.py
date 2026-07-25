from __future__ import annotations

from portfolio.data_science_registry import evaluate_midterm, evaluate_final_project
from portfolio.i18n import t
from portfolio.ui_components import hero_panel, render_safe_table
import streamlit as st


def render() -> None:
    hero_panel(
        title=t("nav_assignments"),
        subtitle=t("subtitle_assignments"),
        kicker=t("section_data_science"),
    )

    st.markdown(
        f"""
<div class="callout">
<strong>{t("nav_projects")}</strong>
<p>{t("nav_docs")}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    midterm = evaluate_midterm()
    final = evaluate_final_project()

    rows = [
        {
            "Project": "Trendyol Data Quality & EDA",
            "Status": "Available",
            "Notebook": "Ready" if midterm["notebook_ready"] else "Pending",
            "Outputs": f"{len(midterm['existing_outputs'])}/{len(midterm['expected_outputs'])}",
            "Colab": "Published" if midterm["colab_configured"] else "Not Published",
            "Note": "Technical completion verified independently from Colab publication",
        },
        {
            "Project": "Trendyol Search Intelligence",
            "Status": "Verified Research System",
            "Notebook": "N/A (Python package)",
            "Outputs": "V1\u2013V5 complete",
            "Colab": "N/A",
            "Note": "V1 persisted champion \u00b7 V3/V3.1 retrieval \u00b7 V4 pipeline \u00b7 V5 cross-encoder \u00b7 51 tests",
        },
    ]

    render_safe_table(
        rows,
        column_map={
            "Project": "Project",
            "Status": "Status",
            "Notebook": "Notebook",
            "Outputs": "Outputs",
            "Colab": "Colab",
            "Note": "Note",
        },
        download_name="academic_archive.csv",
    )

    st.divider()
    st.caption(
        "The Trendyol Search Intelligence project (originally the academic final project) "
        "has been delivered as a full V1\u2013V5 research system. "
        "It is no longer a planned item."
    )

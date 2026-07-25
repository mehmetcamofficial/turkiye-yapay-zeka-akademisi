from __future__ import annotations

from portfolio.data_science_registry import evaluate_midterm, evaluate_final_project
from portfolio.ui_components import hero_panel, render_safe_table
import streamlit as st


def render() -> None:
    hero_panel(
        title="Academic Archive / Akademik Arşiv",
        subtitle="Data science assignments, notebook status, and completed Trendyol Search Intelligence research.",
        kicker="ACADEMIC ARCHIVE",
    )

    st.markdown(
        """
<div class="callout">
<strong>Note / Not</strong>
<p>Academic assignments are separate from the completed Search Intelligence V1–V5 research pipeline.
The Trendyol Search Intelligence system is a verified research system — not an academic planning item.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    midterm = evaluate_midterm()
    final = evaluate_final_project()

    rows = [
        {
            "Project": "Trendyol Data Quality & EDA",
            "Status": "Available / Kullanılabilir",
            "Notebook": "Ready" if midterm["notebook_ready"] else "Pending",
            "Outputs": f"{len(midterm['existing_outputs'])}/{len(midterm['expected_outputs'])}",
            "Colab": "Published" if midterm["colab_configured"] else "Not Published",
            "Note": "Technical completion verified independently from Colab publication",
        },
        {
            "Project": "Trendyol Search Intelligence",
            "Status": "Verified Research System / Doğrulanmış Araştırma Sistemi",
            "Notebook": "N/A (Python package)",
            "Outputs": "V1–V5 complete",
            "Colab": "N/A",
            "Note": "V1 persisted champion · V3/V3.1 retrieval · V4 pipeline · V5 cross-encoder · 51 tests",
        },
    ]

    render_safe_table(
        rows,
        column_map={
            "Project": "Project / Proje",
            "Status": "Status / Durum",
            "Notebook": "Notebook",
            "Outputs": "Outputs / Çıktılar",
            "Colab": "Colab",
            "Note": "Note / Not",
        },
        download_name="academic_archive.csv",
    )

    st.divider()
    st.caption(
        "The Trendyol Search Intelligence project (originally the academic final project) "
        "has been delivered as a full V1–V5 research system. "
        "It is no longer a planned item."
    )

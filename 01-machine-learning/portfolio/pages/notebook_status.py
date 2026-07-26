from __future__ import annotations

from pathlib import Path

import streamlit as st

from portfolio.config import DATA_SCIENCE_MIDTERM_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.ui_components import hero_panel, kpi_grid


def _rel_path(path: str | None) -> str:
    """Convert absolute path to repository-relative path for display."""
    if path is None:
        return "—"
    try:
        p = Path(path)
        repo_root = Path(__file__).resolve().parents[3]  # 01-machine-learning/portfolio/pages
        return str(p.relative_to(repo_root))
    except (ValueError, TypeError):
        return str(path)


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
         _rel_path(midterm["notebook_path"])),
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

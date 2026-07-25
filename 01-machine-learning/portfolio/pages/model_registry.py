from __future__ import annotations

import streamlit as st

from portfolio.i18n import t
from portfolio.project_registry import get_project_registry
from portfolio.ui_components import (hero_panel, kpi_grid, section_heading,
                                     status_badge)


def metadata_status(project: dict) -> bool:
    md = project.get("validation_available", False)
    app = project.get("app_available", False)
    return bool(md or app)


def render() -> None:
    hero_panel(
        title=t("nav_registry"),
        subtitle="All registered projects, research candidates, and artifacts with evidence-backed status.",
        kicker="MODEL OPERATIONS",
    )

    projects = get_project_registry()
    verified = [p for p in projects if p.get("status") == "verified"]
    available = [p for p in projects if p.get("status") == "available"]
    experimental = [p for p in projects if p.get("status") == "experimental"]

    kpi_grid([
        ("Verified", str(len(verified)), "Confirmed champions"),
        ("Available", str(len(available)), "Completed pipelines"),
        ("Experimental", str(len(experimental)), "Research candidates"),
        ("Total", str(len(projects)), "All registered projects"),
    ])

    for project in projects:
        is_experimental = project.get("status") == "experimental"
        decision = "Experimental / Not Promoted" if is_experimental else (
            "Verified" if project.get("status") == "verified" else "Available"
        )
        details = {
            "ID": project.get("id", "—"),
            "Status": status_badge(project.get("status", "experimental")),
            "Decision": decision,
            "Algorithm": project.get("final_model", "—"),
            "Primary Metric": f"{project.get('primary_metric_name', '—')}: {project.get('primary_metric_value', '—')}",
            "Limitations": "; ".join(project.get("limitations", ["—"])[:3]),
        }
        with st.expander(f"{project.get('name', '—')} — {decision}"):
            for k, v in details.items():
                st.markdown(f"**{k}:** {v}", unsafe_allow_html=True)
            artifact_path = project.get("model_path")
            if artifact_path:
                st.markdown(f"**Artifact:** `{artifact_path}`")

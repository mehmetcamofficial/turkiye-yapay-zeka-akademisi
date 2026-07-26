from __future__ import annotations

from pathlib import Path

import streamlit as st

from portfolio.config import ML_ROOT
from portfolio.i18n import t
from portfolio.project_registry import get_project_registry
from portfolio.ui_components import (
    decision_banner, evidence_strip, format_metric, hero_panel,
    information_panel, kpi_grid, section_heading, status_badge,
)


def _rel_path(p: Path | None) -> str:
    if p is None:
        return "—"
    try:
        return str(p.relative_to(ML_ROOT))
    except ValueError:
        return str(p)


def _evidence_status(project: dict) -> str:
    governance = project.get("governance_decision", "")
    if governance:
        return governance
    status = project.get("status", "experimental")
    labels = {
        "verified": t("verified_label"),
        "available": t("available_label"),
        "experimental": t("experimental_label"),
        "local_only": t("local_only_label"),
        "cloud_excluded": t("cloud_excluded_label"),
    }
    return labels.get(status, t("experimental_label"))


def render() -> None:
    hero_panel(
        title=t("nav_model_governance"),
        subtitle=t("subtitle_model_governance"),
        kicker=t("section_search"),
    )

    projects = get_project_registry()

    kpi_grid([
        (t("total"), str(len(projects)), t("all_registered")),
        (t("verified_label"), str(len([p for p in projects if p.get("status") == "verified"])), t("confirmed_champions")),
        (t("available_label"), str(len([p for p in projects if p.get("status") == "available"])), t("completed_pipelines")),
        (t("experimental_label"), str(len([p for p in projects if p.get("status") == "experimental"])), t("research_candidates")),
    ])

    section_heading(t("governance_decisions"), t("governance_decisions_desc"))
    for project in projects:
        name = project.get("name", "—")
        governance = _evidence_status(project)
        prim_val = project.get("primary_metric_value")
        prim_str = format_metric(prim_val) if prim_val is not None else "—"
        with st.expander(f"{name} — {governance}", expanded=False):
            st.markdown(f"**{t('id_label')}:** `{project.get('id', '—')}`")
            st.markdown(f"**{t('status_label')}:** `{project.get('status', '—')}`")
            st.markdown(f"**{t('decision_label')}:** {governance}")
            st.markdown(f"**{t('algorithm_label')}:** {project.get('final_model', '—')}")
            st.markdown(f"**{t('metric_label')}:** {project.get('primary_metric_name', '—')}: {prim_str}")
            limitations = project.get("limitations", [])
            if limitations:
                st.markdown(f"**{t('limitations_label')}:** " + "; ".join(limitations[:3]))
            artifact_path = project.get("model_path")
            if artifact_path:
                st.markdown(f"**{t('artifact_label')}:** `{_rel_path(artifact_path)}`")

    decision_banner(
        t("governance_not_prod"),
        t("not_production_promoted_desc"),
    )

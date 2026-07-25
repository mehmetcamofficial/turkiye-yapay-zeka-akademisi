from __future__ import annotations

import streamlit as st
import pandas as pd

from portfolio.i18n import t
from portfolio.project_registry import get_project_registry
from portfolio.ui_components import (format_metric, hero_panel,
                                     section_heading, status_badge)


def render() -> None:
    hero_panel(
        title=t("nav_projects"),
        subtitle=t("subtitle_projects"),
        kicker=t("section_portfolio"),
    )

    projects = get_project_registry()

    rows = []
    for p in projects:
        primary = p.get("primary_metric_value")
        primary_str = format_metric(primary)
        rows.append({
            "Project": p.get("name", "—"),
            "Category": p.get("category", "—"),
            "Status": status_badge(p.get("status", "experimental")),
            "Model": p.get("final_model", "—"),
            "Metric": f"{p.get('primary_metric_name', '—')}: {primary_str}",
            "Limitations": "; ".join(p.get("limitations", [])[:2]),
        })

    for row in rows:
        cols = st.columns([3, 1.5, 0.8, 1.5, 1.5, 2])
        cols[0].markdown(f"**{row['Project']}**")
        cols[1].markdown(row["Category"])
        cols[2].markdown(row["Status"], unsafe_allow_html=True)
        cols[3].markdown(row["Model"])
        cols[4].markdown(row["Metric"])
        cols[5].markdown(row["Limitations"])
        st.divider()

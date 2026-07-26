from __future__ import annotations

from pathlib import Path

import streamlit as st

from portfolio.config import DATA_SCIENCE_MIDTERM_DIR, TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.ui_components import hero_panel, kpi_grid, information_panel

CANONICAL_FILES = [
    "cardinality_summary.csv", "categorical_summary.csv", "column_profile.csv",
    "data_quality_report.json", "data_type_summary.csv", "duplicate_summary.csv",
    "missing_values.csv", "numeric_summary.csv", "profile_summary.md",
    "schema_report.json", "table_summary.csv", "text_length_summary.csv",
]


def _rel_path(path: str | None) -> str:
    if path is None:
        return "—"
    try:
        p = Path(path)
        repo_root = Path(__file__).resolve().parents[3]
        return str(p.relative_to(repo_root))
    except (ValueError, TypeError):
        return str(path)


def _profile_outputs_count() -> int:
    outputs_dir = TRENDYOL_PROFILE_DIR / "outputs"
    if not outputs_dir.is_dir():
        return 0
    return sum(1 for f in CANONICAL_FILES if (outputs_dir / f).is_file())


def render() -> None:
    hero_panel(
        title=t("nav_notebook_status"),
        subtitle=t("subtitle_notebook_status"),
        kicker=t("section_portfolio"),
    )

    midterm = evaluate_midterm()
    profile_count = _profile_outputs_count()

    kpi_grid([
        (t("local_dataset"), t("status_available") if midterm["dataset_path"] else t("status_unavailable"),
         f"{midterm['downloaded_file_count']} {t('files_locally')}"),
        (t("notebook_label"), t("status_available") if midterm["notebook_ready"] else t("status_unavailable"),
         _rel_path(midterm["notebook_path"])),
        (t("profile_outputs"), f"{profile_count}/{len(CANONICAL_FILES)}",
         t("profile_outputs_available")),
        (t("schema_compatibility"), t("compatible") if midterm["schema_compatible"] else t("partial_compatibility"),
         f"{len(midterm['available_columns'])}/{len(midterm['required_columns'])} {t('schema_fields')}"),
    ])

    col1, col2 = st.columns(2)
    with col1:
        information_panel(t("notebook_exec_status"),
                          t("notebook_executed_yes") if midterm["notebook_ready"] else t("notebook_executed_no"))
        if midterm["notebook_path"]:
            nb_path = Path(midterm["notebook_path"])
            if nb_path.is_file():
                with open(nb_path, "rb") as f:
                    st.download_button(
                        t("download_ipynb"),
                        f.read(),
                        nb_path.name,
                        "application/x-ipynb+json",
                    )

    with col2:
        information_panel(t("source_dataset_state"),
                          t("source_local") if midterm["dataset_path"] else t("source_not_available"))
        profile_zip_path = TRENDYOL_PROFILE_DIR / "outputs"
        if profile_zip_path.is_dir():
            import io
            import zipfile
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                for fname in CANONICAL_FILES:
                    fpath = profile_zip_path / fname
                    if fpath.is_file():
                        zf.write(str(fpath), fname)
            buf.seek(0)
            st.download_button(
                t("download_profile_outputs"),
                buf,
                "trendyol_profile_outputs.zip",
                "application/zip",
            )

    colab_url = midterm.get("colab_url", "")
    if colab_url and "github.com" in colab_url.lower():
        st.link_button(t("open_in_colab"), colab_url)
    else:
        st.info(t("colab_not_configured"))

    st.caption(
        f"{t('profile_outputs')}: {profile_count}/{len(CANONICAL_FILES)} | "
        f"{t('notebook_path')}: {_rel_path(midterm['notebook_path'])} | "
        f"{t('source_dataset_state')}: {t('source_local') if midterm['dataset_path'] else t('source_not_available')}"
    )

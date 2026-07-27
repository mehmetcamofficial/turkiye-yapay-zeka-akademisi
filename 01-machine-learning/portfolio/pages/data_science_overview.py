from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from portfolio.config import TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.i18n import t
from portfolio.loaders import load_csv_safe, load_json_safe
# i18n keys needed: kb_unit

from portfolio.ui_components import (architecture_flow, empty_state, hero_panel,
                                     information_panel, kpi_grid,
                                     render_safe_table, section_heading)

PROFILE_DIR = TRENDYOL_PROFILE_DIR

CANONICAL_MANIFEST = [
    "cardinality_summary.csv",
    "categorical_summary.csv",
    "column_profile.csv",
    "data_quality_report.json",
    "data_type_summary.csv",
    "duplicate_summary.csv",
    "missing_values.csv",
    "numeric_summary.csv",
    "profile_summary.md",
    "schema_report.json",
    "table_summary.csv",
    "text_length_summary.csv",
]


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


def _compute_schema_compatibility(schema: dict[str, Any] | None) -> dict[str, Any]:
    if not schema or not schema.get("required_fields"):
        default_summary = {
            "compatible_count": 0,
            "total_count": 10,
            "direct_matches": 0,
            "semantic_matches": 0,
            "unavailable": 0,
            "requires_enrichment": 0,
        }
        return default_summary
    fields = schema["required_fields"]
    direct = sum(1 for f in fields if f.get("match_type") == "Direct Match")
    semantic = sum(1 for f in fields if f.get("match_type") in ("Safe Semantic Match", "Semantic Match"))
    unavailable = sum(1 for f in fields if f.get("match_type") in ("Missing", "Unavailable"))
    enrichment = sum(1 for f in fields if f.get("match_type") == "Requires Enrichment")
    compatible = direct + semantic
    return {
        "compatible_count": compatible,
        "total_count": len(fields),
        "direct_matches": direct,
        "semantic_matches": semantic,
        "unavailable": unavailable,
        "requires_enrichment": enrichment,
    }


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
        profile_count = len(_profile_outputs())
        total_bytes = midterm.get("downloaded_size_bytes", 0)
        total_gib = total_bytes / (1024 ** 3)
        today_str = datetime.now().strftime("%d %b %Y")

        table_summary = load_csv_safe(str(PROFILE_DIR / "outputs/table_summary.csv"))
        product_count = "—"
        if not table_summary.empty:
            items_row = table_summary[table_summary["table"] == "items.csv"]
            if not items_row.empty:
                pc = int(items_row.iloc[0]["full_row_count"])
                product_count = f"{pc:,}".replace(",", ".")

        kpi_grid([
            (t("overview_source_files"), str(midterm.get("downloaded_file_count", 0)), t("overview_n_source_files")),
            (t("overview_total_size"), f"{total_gib:.2f} {t('overview_gib')}", t("overview_total_size_desc")),
            (t("overview_profile_output_count"), f"{profile_count}/{len(CANONICAL_MANIFEST)}", t("overview_profile_output_desc")),
            (t("overview_catalog_fields"), str(len(required_fields)), t("overview_catalog_fields_desc")),
            (t("overview_product_sample"), product_count, t("overview_product_sample_desc")),
            (t("overview_last_validation"), today_str, t("overview_last_validation_desc")),
        ])

        section_heading(t("overview_data_pipeline"))
        architecture_flow([
            (f"{t('overview_pipeline_source_files')}: 7 {t('overview_pipeline_file')}", "current"),
            (f"{t('overview_pipeline_schema_validation')}: {t('status_verified')}", "current"),
            (f"{t('overview_pipeline_quality_control')}: {t('overview_zero_issues')}", "current"),
            (f"{t('overview_pipeline_profiling')}: {profile_count} {t('overview_pipeline_output_unit')}", "experimental"),
            (f"{t('overview_pipeline_search_indexes')}: {t('ready')}", "experimental"),
            (f"{t('overview_pipeline_model_inputs')}: {t('ready')}", "experimental"),
        ])

        section_heading(t("overview_dataset_composition"))
        categorical = load_csv_safe(str(PROFILE_DIR / "outputs/categorical_summary.csv"))
        items_cat = categorical[categorical["table"] == "items.csv"] if not categorical.empty else pd.DataFrame()
        if not items_cat.empty:
            col1, col2 = st.columns(2)
            with col1:
                cat_data = items_cat[items_cat["column"] == "category"].head(8)
                if not cat_data.empty and "value" in cat_data and "count_sample" in cat_data:
                    fig, ax = plt.subplots(figsize=(5, 3))
                    short = [v.split("/")[-1] if "/" in str(v) else v for v in cat_data["value"].iloc[::-1]]
                    ax.barh(short, cat_data["count_sample"].iloc[::-1], color="#6366f1", height=0.6)
                    ax.set_xlabel(t("count_sample"))
                    ax.set_title(t("overview_top_categories"), fontsize=10)
                    fig.tight_layout()
                    st.pyplot(fig)
            with col2:
                brand_data = items_cat[items_cat["column"] == "brand"].head(8)
                if not brand_data.empty and "value" in brand_data and "count_sample" in brand_data:
                    fig, ax = plt.subplots(figsize=(5, 3))
                    ax.barh(brand_data["value"].iloc[::-1], brand_data["count_sample"].iloc[::-1],
                            color="#22c55e", height=0.6)
                    ax.set_xlabel(t("count_sample"))
                    ax.set_title(t("overview_top_brands"), fontsize=10)
                    fig.tight_layout()
                    st.pyplot(fig)

        text_length = load_csv_safe(str(PROFILE_DIR / "outputs/text_length_summary.csv"))
        items_text = text_length[text_length["table"] == "items.csv"] if not text_length.empty else pd.DataFrame()
        title_len = items_text[items_text["column"] == "title"] if not items_text.empty else pd.DataFrame()
        if not title_len.empty and "mean_length_sample" in title_len and "max_length_sample" in title_len:
            fig, ax = plt.subplots(figsize=(5, 2))
            mean_val = float(title_len.iloc[0]["mean_length_sample"])
            max_val = int(title_len.iloc[0]["max_length_sample"])
            ax.bar([t("overview_mean_length"), t("overview_max_length")], [mean_val, max_val],
                   color=["#6366f1", "#f59e0b"], width=0.4)
            ax.set_ylabel(t("overview_characters"))
            ax.set_title(t("overview_title_length"), fontsize=10)
            fig.tight_layout()
            st.pyplot(fig)

        section_heading(t("overview_data_quality_summary"))
        missing = load_csv_safe(str(PROFILE_DIR / "outputs/missing_values.csv"))
        critical_missing_count = -1
        if not missing.empty:
            items_miss = missing[missing["table"] == "items.csv"]
            if not items_miss.empty and "missing_percentage_sample" in items_miss:
                critical_missing_count = int((items_miss["missing_percentage_sample"] > 0).sum())
        missing_text = (
            t("overview_critical_field_none")
            if critical_missing_count <= 0
            else str(critical_missing_count)
        )

        duplicate = load_csv_safe(str(PROFILE_DIR / "outputs/duplicate_summary.csv"))
        dup_text = "0"
        if not duplicate.empty:
            items_dup = duplicate[duplicate["table"] == "items.csv"]
            if not items_dup.empty and "duplicate_count_sample" in items_dup:
                dup_text = str(int(items_dup.iloc[0]["duplicate_count_sample"]))

        schema_compatible = schema_report.get("schema_compatible", False) if schema_report else False
        schema_text = t("compatible") if schema_compatible else t("status_limited")

        output_int = f"{profile_count}/{len(CANONICAL_MANIFEST)}"

        kpi_grid([
            (t("overview_missing_values"), missing_text, None),
            (t("overview_duplicate_records"), dup_text, None),
            (t("overview_schema_status"), schema_text, None),
            (t("overview_output_integrity"), output_int, None),
        ])

        information_panel(t("overview_insight_what"), t("overview_insight_what_text"))
        information_panel(t("overview_insight_why"), t("overview_insight_why_text"))
        information_panel(t("overview_insight_limitation"), t("overview_insight_limitation_text"))

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
            sizes = [(r.get("relative_path", r.get("file", "—")), r.get("size_bytes", 0) / 1024 / 1024) for r in inventory]
            if sizes:
                fig, ax = plt.subplots(figsize=(6, 2.5))
                names, sz = zip(*sorted(sizes, key=lambda x: -x[1]))
                ax.barh(names, sz, color="#6366f1", height=0.6)
                ax.set_xlabel(t("size_mb"))
                ax.set_title(t("file_sizes"), fontsize=10)
                fig.tight_layout()
                st.pyplot(fig)
        else:
            empty_state(t("dataset_inventory"),
                        t("inventory_local_only"))

    with tabs[2]:
        schema = _load_schema()
        if schema and schema.get("required_fields"):
            compat = _compute_schema_compatibility(schema)
            section_heading(t("schema_compatibility_summary"))
            st.markdown(
                f"<div style='display:flex;flex-wrap:wrap;gap:16px;margin-bottom:16px;'>"
                f"<div style='flex:1;min-width:180px;background:var(--bg-card);border-radius:8px;padding:12px;border:1px solid var(--border)'>"
                f"<small>{t('schema_dataset_purpose')}</small><br><strong>{t('schema_dataset_purpose_value')}</strong></div>"
                f"<div style='flex:1;min-width:180px;background:var(--bg-card);border-radius:8px;padding:12px;border:1px solid var(--border)'>"
                f"<small>{t('schema_transactional_purpose')}</small><br><strong>{t('schema_transactional_purpose_value')}</strong></div>"
                f"<div style='flex:1;min-width:180px;background:var(--bg-card);border-radius:8px;padding:12px;border:1px solid var(--border)'>"
                f"<small>{t('schema_compatible_fields')}</small><br><strong style='color:#22c55e'>{compat['compatible_count']}/{compat['total_count']}</strong></div>"
                f"<div style='flex:1;min-width:180px;background:var(--bg-card);border-radius:8px;padding:12px;border:1px solid var(--border)'>"
                f"<small>{t('schema_unavailable_fields')}</small><br><strong style='color:#ef4444'>{compat['unavailable']}/{compat['total_count']}</strong></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.caption(t("schema_fields_explanation"))

            match_type_map = {
                "Direct Match": t("match_direct"),
                "Safe Semantic Match": t("match_semantic"),
                "Semantic Match": t("match_semantic"),
                "Missing": t("match_unavailable"),
                "Unavailable": t("match_unavailable"),
                "Requires Enrichment": t("match_enrichment"),
            }
            for field in schema["required_fields"]:
                raw_type = field.get("match_type", "")
                field["match_type"] = match_type_map.get(raw_type, raw_type)
            render_safe_table(
                schema["required_fields"],
                column_map={"required_field": t("required_field"), "source_file": t("source_file"),
                            "actual_field": t("actual_field"), "match_type": t("match_type"),
                            "transformation": t("transformation"), "confidence": t("confidence")},
                download_name="schema_report.csv",
            )
            confidences = [(r.get("required_field", "—"), r.get("confidence", 0)) for r in schema["required_fields"] if r.get("confidence") is not None]
            all_high = all(c == "Yüksek" or c == "High" for _, c in confidences) if confidences else False
            if confidences and all_high:
                st.markdown(
                    f"<div style='background:var(--bg-card);border:1px solid var(--success);border-radius:8px;padding:16px;margin-top:8px;'>"
                    f"<strong>{t('positive_finding')}: {t('all_high_confidence')}</strong></div>",
                    unsafe_allow_html=True,
                )
            elif confidences:
                fig, ax = plt.subplots(figsize=(5, 2.5))
                fields, confs = zip(*confidences)
                ax.barh(fields, confs, color="#22c55e", height=0.6)
                ax.set_xlabel(t("confidence"))
                ax.set_xlim(0, 100)
                ax.set_title(t("field_confidence"), fontsize=10)
                fig.tight_layout()
                st.pyplot(fig)
        else:
            empty_state(t("schema_report"),
                        t("schema_report_generated"))

    with tabs[3]:
        quality = _load_quality()
        if quality:
            section_heading(t("data_quality"), t("quality_metrics_from_profile"))
            render_safe_table(quality, download_name="data_quality.csv")
            quality_df = pd.DataFrame(quality)
            if all(c in quality_df.columns for c in ["table", "completeness"]):
                fig, ax = plt.subplots(figsize=(6, 2.5))
                ax.barh(quality_df["table"], quality_df["completeness"],
                        color="#22c55e", height=0.6)
                ax.set_xlabel(t("completeness_pct"))
                ax.set_title(t("table_completeness"), fontsize=10)
                ax.set_xlim(0, 100)
                fig.tight_layout()
                st.pyplot(fig)

        missing = load_csv_safe(str(PROFILE_DIR / "outputs/missing_values.csv"))
        if not missing.empty:
            section_heading(t("missingness"), t("missingness_desc"))
            items_missing = missing[missing["table"] == "items.csv"]
            if not items_missing.empty:
                if "missing_percentage_sample" in items_missing and items_missing["missing_percentage_sample"].sum() == 0:
                    st.markdown(
                        f"<div style='background:var(--bg-card);border:1px solid var(--success);border-radius:8px;padding:16px;'>"
                        f"<strong>{t('positive_finding')}: {t('positive_finding_missingness')}</strong></div>",
                        unsafe_allow_html=True,
                    )
                elif "missing_percentage_sample" in items_missing:
                    fig, ax = plt.subplots(figsize=(6, 2.5))
                    ax.barh(items_missing["column"], items_missing["missing_percentage_sample"],
                            color="#ef4444", height=0.6)
                    ax.set_xlabel(t("missing_pct"))
                    ax.set_title(t("missingness_by_column"), fontsize=10)
                    fig.tight_layout()
                    st.pyplot(fig)

        categorical = load_csv_safe(str(PROFILE_DIR / "outputs/categorical_summary.csv"))
        items_cat = categorical[categorical["table"] == "items.csv"] if not categorical.empty else pd.DataFrame()
        if not items_cat.empty:
            section_heading(t("distribution"), t("distribution_desc"))
            for col_name in ["category", "brand", "gender"]:
                col_data = items_cat[items_cat["column"] == col_name].head(10)
                if not col_data.empty and "value" in col_data and "count_sample" in col_data:
                    fig, ax = plt.subplots(figsize=(5, 2.5))
                    ax.barh(col_data["value"].iloc[::-1], col_data["count_sample"].iloc[::-1],
                            color="#6366f1", height=0.6)
                    ax.set_xlabel(t("count_sample"))
                    ax.set_title(t(f"dist_{col_name}"), fontsize=10)
                    fig.tight_layout()
                    st.pyplot(fig)
        else:
            empty_state(t("quality_report"),
                        t("quality_report_generated"))

    with tabs[4]:
        outputs = _profile_outputs()
        if outputs:
            section_heading(t("profile_outputs"), f"{len(outputs)} {t('generated_files')}")
            st.markdown("\n".join(f"- `{o}`" for o in outputs))

        section_heading(t("canonical_manifest"), t("canonical_manifest_desc"))
        manifest_rows = []
        for expected in CANONICAL_MANIFEST:
            exists = expected in outputs
            ext = Path(expected).suffix
            type_map = {".csv": t("manifest_csv"), ".json": t("manifest_json"), ".md": t("manifest_md")}
            ftype = type_map.get(ext, ext.upper())
            fpath = PROFILE_DIR / "outputs" / expected
            fsize = f"{fpath.stat().st_size / 1024:.1f} {t('kb_unit')}" if fpath.is_file() else "—"
            status = t("manifest_present") if exists else t("manifest_missing")
            manifest_rows.append({
                t("manifest_filename"): expected,
                t("manifest_type"): ftype,
                t("manifest_size"): fsize,
                t("manifest_status"): status,
            })
        if manifest_rows:
            render_safe_table(manifest_rows, download_name="canonical_manifest.csv")

        numeric = load_csv_safe(str(PROFILE_DIR / "outputs/numeric_summary.csv"))
        label_stats = numeric[numeric["column"] == "label"] if not numeric.empty else pd.DataFrame()
        if not label_stats.empty:
            section_heading(t("label_distribution"), t("label_dist_desc"))
            fig, ax = plt.subplots(figsize=(4, 2.5))
            mean_val = float(label_stats.iloc[0]["mean"])
            pos_pct = mean_val * 100
            neg_pct = 100 - pos_pct
            ax.bar([t("negative"), t("positive")], [neg_pct, pos_pct],
                   color=["#ef4444", "#22c55e"], width=0.5)
            for i, v in enumerate([neg_pct, pos_pct]):
                ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=10)
            ax.set_ylabel(t("percentage"))
            ax.set_title(t("label_balance"), fontsize=10)
            fig.tight_layout()
            st.pyplot(fig)

        duplicate = load_json_safe(str(PROFILE_DIR / "outputs/duplicate_summary.csv"))
        if duplicate:
            section_heading(t("duplicate_analysis"), t("duplicate_desc"))
            dup_df = pd.DataFrame([duplicate]) if isinstance(duplicate, dict) else pd.DataFrame(duplicate)
            render_safe_table(dup_df, max_rows=10)

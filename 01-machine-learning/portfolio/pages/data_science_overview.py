"""Lazy, saved-artifact Data Science workspace."""

from __future__ import annotations

import importlib
import sys

import pandas as pd
import streamlit as st

from portfolio.config import DATA_SCIENCE_MIDTERM_DIR, TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.loaders import load_csv_safe, load_json_safe, load_text_safe
from portfolio.ui_components import empty_state_panel, hero_panel, information_panel, metric_table, section_heading, status_badge


def _refresh_saved_profile(item: dict) -> None:
    """Run bounded profiling only after an explicit click; never at import/startup."""
    try:
        sys.path.insert(0, str(TRENDYOL_PROFILE_DIR))
        try:
            module = importlib.import_module("src.reporting")
            module.generate_profiles(DATA_SCIENCE_MIDTERM_DIR/"data", item["inventory"], TRENDYOL_PROFILE_DIR/"outputs", max_rows=20_000)
        finally:
            sys.path.remove(str(TRENDYOL_PROFILE_DIR))
        st.cache_data.clear()
        st.success("Bounded profil kaydedildi. Dağılım metrikleri sampled olarak etiketlendi.")
    except Exception:
        st.error("Profil oluşturulamadı. Teknik logları kontrol edin.")


def render() -> None:
    item=evaluate_midterm(); inventory=item["inventory"]
    hero_panel("Data Science Workspace", "Trendyol veri varlıkları, gerçek şemalar, bounded kalite profilleri ve notebook hazırlığı.", "DATA ANALYTICS")
    tabs=st.tabs(["Overview","Dataset Inventory","Schema Compatibility","Data Quality","Exploratory Analysis","Notebook","Outputs","Technical Details"])
    with tabs[0]:
        columns=st.columns(6)
        values=[("Source","Kaggle"), ("Download","Ready" if inventory else "Missing"), ("Files",len(inventory)),
                ("Total size",f"{item['downloaded_size_bytes']/1024**3:.2f} GB"), ("Tables",sum(r['extension'] in {'.csv','.parquet','.xlsx'} for r in inventory)),
                ("Schema","Adapted" if inventory else "Missing")]
        for column,(label,value) in zip(columns,values): column.metric(label,value)
        information_panel("Assignment support", f"Supported questions: {item['supported_questions']} · Blocked: {item['blocked_questions']}")
        information_panel("Sonuç", "İndirilen veri gerçek ürün kataloğu ve search relevance EDA kapsamına uyarlandı; transactional müşteri/sipariş alanları üretilmedi.")
        if st.button("Profili oluştur / yenile", key="generate_trendyol_profile", use_container_width=True):
            with st.spinner("20.000 satırlık deterministic samples profilleniyor..."):
                _refresh_saved_profile(item)
    with tabs[1]:
        if not inventory: empty_state_panel("Inventory missing","Run trendyol-profile/run_profile.py explicitly.")
        else:
            frame=pd.DataFrame(inventory); frame["size_mb"]=frame["size_bytes"]/1024**2; frame["sha256_short"]=frame["sha256"].str[:12]
            metric_table(frame[["relative_path","extension","size_mb","row_count","column_count","sha256_short","readable"]])
    with tabs[2]:
        report=load_json_safe(str(TRENDYOL_PROFILE_DIR/"outputs/schema_report.json"))
        fields=pd.DataFrame(report.get("required_fields",[]))
        metric_table(fields,"Schema report has not been generated.")
        if report: information_panel("Supported / blocked",f"Supported: {report['supported_questions']} · Blocked: {report['blocked_questions']}")
    with tabs[3]:
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR/"outputs/missing_values.csv")),"Missing-value profile unavailable.")
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR/"outputs/duplicate_summary.csv")),"Duplicate profile unavailable.")
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR/"outputs/data_type_summary.csv")),"Type profile unavailable.")
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR/"outputs/cardinality_summary.csv")),"Cardinality profile unavailable.")
    with tabs[4]:
        section_heading("Numeric summaries","All distribution metrics show their sampled scope.")
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR/"outputs/numeric_summary.csv")))
        section_heading("Categorical distributions")
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR/"outputs/categorical_summary.csv")))
        section_heading("Text length")
        metric_table(load_csv_safe(str(TRENDYOL_PROFILE_DIR/"outputs/text_length_summary.csv")))
    with tabs[5]:
        notebook=item["notebook_path"]
        st.markdown(status_badge("Hazır" if item["notebook_ready"] else "Veri Bekleniyor"),unsafe_allow_html=True)
        information_panel("Question readiness",f"Completed: {item['completed_questions']}/15 · Supported by Trendyol schema: {len(item['supported_questions'])}/15")
        information_panel("Colab","Not configured" if not item["colab_configured"] else item["colab_url"])
        if notebook.is_file(): st.download_button("Download notebook",notebook.read_bytes(),notebook.name,"application/x-ipynb+json")
    with tabs[6]:
        output_rows=[]
        for path in sorted((TRENDYOL_PROFILE_DIR/"outputs").glob("*")):
            if path.is_file() and path.name != ".gitkeep": output_rows.append({"output":path.name,"size_bytes":path.stat().st_size,"status":"Ready"})
        metric_table(pd.DataFrame(output_rows),"No saved profile outputs.")
        information_panel("Clean transactional dataset","Unavailable because the Trendyol schema is not compatible with the academy midterm.")
    with tabs[7]:
        with st.expander("Full hashes and generation metadata",expanded=False):
            if inventory: metric_table(pd.DataFrame(inventory)[["relative_path","sha256","encoding","columns"]])
            st.markdown(load_text_safe(str(TRENDYOL_PROFILE_DIR/"outputs/profile_summary.md")))
        with st.expander("Local artifact locations",expanded=False):
            st.code("02-data-science/midterm-assignment/data/\n02-data-science/midterm-assignment/outputs/dataset_inventory.json\n02-data-science/trendyol-profile/outputs/",language="text")

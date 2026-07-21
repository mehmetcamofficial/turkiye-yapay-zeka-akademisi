"""Verified professional profile and working approach."""
import streamlit as st
from portfolio.ui_components import evidence_strip,external_action,information_panel,page_header,section_heading

def render():
    page_header("About Mehmet Cam","AI engineering, machine learning, data science and product-oriented technical projects—presented through runnable systems and verifiable evidence.","PROFESSIONAL PROFILE")
    section_heading("Professional Focus")
    evidence_strip([("AI Engineering","End-to-end systems","Training to inference"),("Machine Learning","Classification + regression","Evaluation first"),("Data Science","Profiling + quality","Reproducible analysis"),("Search & NLP","Relevance + ranking","Lexical baselines"),("Research","Champion/challenger","Honest uncertainty")])
    section_heading("What This Platform Demonstrates")
    information_panel("Applied systems","Customer churn, housing forecasting, sentiment classification and query-product search relevance are connected to local artifacts and live interfaces.")
    information_panel("Model operations","Registry, artifact health, checksums, fresh-process reload, metadata and bounded batch inference make operational assumptions visible.")
    section_heading("Working Approach")
    evidence_strip([("1","Problem formulation","Decision and metric first"),("2","Data validation","Schema and provenance"),("3","Leakage prevention","Group-aware split"),("4","Baseline first","Complexity earns promotion"),("5","Governance","Holdout + uncertainty"),("6","Delivery","User-focused, bounded UX")])
    section_heading("Selected Projects")
    st.markdown("- Trendyol Search & Product Intelligence\n- Customer Churn Intelligence\n- Housing Value Forecasting\n- Sentiment Intelligence")
    section_heading("Professional Links")
    cols=st.columns(3)
    with cols[0]: external_action("Personal website","https://mehmetcamofficial.com.tr/")
    with cols[1]: external_action("LinkedIn","https://www.linkedin.com/in/mehmet-cam09/")
    with cols[2]: external_action("GitHub","https://github.com/mehmetcamofficial")
    st.caption("No employment history, client work or commercial production claim is inferred by this page.")

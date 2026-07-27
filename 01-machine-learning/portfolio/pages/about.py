"""Verified professional profile and working approach."""
import streamlit as st
from portfolio.i18n import t
from portfolio.ui_components import evidence_strip,external_action,information_panel,page_header,section_heading

def render():
    page_header(t("about_title"),t("about_subtitle"),"PROFESSIONAL PROFILE")
    section_heading(t("about_section_focus"))
    evidence_strip([(t("about_ai_eng"),t("about_e2e"),t("about_train_inf")),(t("about_ml"),t("about_class_reg"),t("about_eval_first")),(t("about_ds"),t("about_profiling"),t("about_repro")),(t("about_search_nlp"),t("about_relevance"),t("about_lexical")),(t("about_research"),t("about_champ"),t("about_honest"))])
    section_heading(t("about_section_demo"))
    information_panel(t("about_applied"),t("about_applied_desc"))
    information_panel(t("about_model_ops"),t("about_model_ops_desc"))
    section_heading(t("about_section_approach"))
    evidence_strip([("1","Problem formulation","Decision and metric first"),("2","Data validation","Schema and provenance"),("3","Leakage prevention","Group-aware split"),("4","Baseline first","Complexity earns promotion"),("5","Governance","Holdout + uncertainty"),("6","Delivery","User-focused, bounded UX")])
    section_heading(t("about_section_projects"))
    st.markdown("- Trendyol Search & Product Intelligence\n- Customer Churn Intelligence\n- Housing Value Forecasting\n- Sentiment Intelligence")
    section_heading(t("about_section_links"))
    cols=st.columns(3)
    with cols[0]: external_action("Personal website","https://mehmetcamofficial.com.tr/")
    with cols[1]: external_action("LinkedIn","https://www.linkedin.com/in/mehmet-cam09/")
    with cols[2]: external_action("GitHub","https://github.com/mehmetcamofficial")
    st.caption(t("about_disclaimer"))

"""Fully integrated UCI sentiment-analysis module."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import streamlit as st

from portfolio.config import NLP_DIR, NLP_MODEL_PATH
from portfolio.i18n import t
from portfolio.loaders import (load_csv_safe, load_image_path_safe,
                               load_json_safe, load_model_safe, load_text_safe)
from portfolio.project_registry import project_by_id
from portfolio.ui_components import (artifact_checklist, classification_report_frame, empty_state_panel,
                                     hero_panel, information_panel, metric_table,
                                     prediction_result_card, render_safe_table, section_heading)


def _clean_text(text: str) -> str:
    value = re.sub(r"<[^>]+>", " ", str(text))
    value = re.sub(r"https?://\S+|www\.\S+", " URL ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def _model():
    return load_model_safe(NLP_MODEL_PATH)


def _confidence(model, texts: list[str] | pd.Series) -> np.ndarray | None:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(texts).max(axis=1)
    if hasattr(model, "decision_function"):
        score = np.abs(model.decision_function(texts))
        return 1 / (1 + np.exp(-score))
    return None


def _single() -> None:
    model_result = _model()
    text = st.text_area(t("nlp_text_input"), "This product works perfectly and I love it.", height=130)
    if st.button(t("nlp_analyze"), key="nlp_single_predict"):
        if not model_result.ok:
            st.error(model_result.public_message); return
        model = model_result.model
        prepared = [_clean_text(text)]
        if not prepared[0]:
            st.warning(t("nlp_empty_text")); return
        try:
            label = int(model.predict(prepared)[0]); scores = _confidence(model, prepared)
            detail = t("nlp_binary_note")
            if scores is not None:
                detail += " " + t("nlp_score", score=float(scores[0]))
            prediction_result_card(t("nlp_predicted"), t("nlp_positive") if label == 1 else t("nlp_negative"), detail)
        except Exception:
            st.error(t("nlp_analysis_failed"))


def _batch() -> None:
    model_result = _model()
    uploaded = st.file_uploader(t("nlp_upload_csv"), type="csv", key="nlp_batch")
    if uploaded is None:
        information_panel(t("nlp_batch_pred"), t("nlp_batch_desc"))
        return
    try:
        frame = pd.read_csv(uploaded)
    except (UnicodeError, pd.errors.ParserError):
        st.error(t("nlp_csv_error")); return
    if frame.empty or not len(frame.columns):
        st.error(t("nlp_no_data")); return
    default_index = list(frame.columns).index("text") if "text" in frame else 0
    text_column = st.selectbox(t("nlp_text_col"), list(frame.columns), index=default_index)
    if st.button(t("nlp_run_batch"), key="nlp_batch_predict"):
        if not model_result.ok:
            st.error(model_result.public_message); return
        model = model_result.model
        prepared = frame[text_column].fillna("").map(_clean_text)
        try:
            result = frame.copy(); result["sentiment_label"] = model.predict(prepared)
            result["sentiment"] = result["sentiment_label"].map({0: t("nlp_negative"), 1: t("nlp_positive")})
            scores = _confidence(model, prepared)
            if scores is not None: result["confidence"] = scores
            render_safe_table(result, max_rows=100)
            st.download_button(t("nlp_download_results"), result.to_csv(index=False).encode("utf-8"),
                               "sentiment_predictions.csv", "text/csv")
        except Exception:
            st.error(t("nlp_batch_failed"))


def _performance() -> None:
    for title, filename in [(t("nlp_final_metrics"), "test_metrics.csv"),
                            (t("nlp_validation"), "validation_results.csv"),
                            (t("nlp_cv"), "cross_validation_results.csv")]:
        section_heading(title); metric_table(load_csv_safe(str(NLP_DIR / "outputs" / filename)))
    section_heading(t("nlp_best_params"))
    payload = load_json_safe(str(NLP_DIR / "outputs/best_hyperparameters.json"))
    st.json(payload) if payload else empty_state_panel(t("nlp_json_missing"), t("nlp_tuning_missing"))
    with st.expander(t("nlp_gridsearch"), expanded=False):
        metric_table(load_csv_safe(str(NLP_DIR / "outputs/hyperparameter_search_results.csv")))
    report = load_text_safe(str(NLP_DIR / "outputs/classification_report.txt"))
    if report: metric_table(classification_report_frame(report))
    image = load_image_path_safe(str(NLP_DIR / "outputs/confusion_matrix.png"))
    if image: st.image(image, use_column_width=True)


def render() -> None:
    hero_panel(
        title=t("ml_section_nlp"),
        subtitle=t("subtitle_nlp"),
        kicker=t("section_ml"),
    )
    tabs = st.tabs([t("tab_overview"), t("tab_single_prediction"), t("tab_batch_csv"), t("tab_model_performance"), t("tab_word_effects"), t("tab_error_analysis"), t("tab_data_source")])
    with tabs[0]:
        project = project_by_id("nlp")
        metrics = load_csv_safe(str(NLP_DIR / "outputs/test_metrics.csv"))
        columns = st.columns(4)
        for column, name in zip(columns, ["Accuracy", "Precision", "Recall", "F1"]):
            value = float(metrics.iloc[0][name]) if not metrics.empty and name in metrics else None
            column.metric(name, "—" if value is None else f"{value:.4f}")
        information_panel(t("purpose"), project["description"])
        information_panel(t("data_model"), f"{project['dataset']} ({project['dataset_size']}) · {project['final_model']}")
        information_panel(t("workflow"), "Yerel UCI CSV → deterministik temizlik → TF-IDF → stratified CV → tuning → dokunulmamış test")
        information_panel(t("limitations"), "; ".join(project["limitations"]))
        with st.expander(t("tab_technical"), expanded=False):
            artifact_checklist(project)
    with tabs[1]: _single()
    with tabs[2]: _batch()
    with tabs[3]: _performance()
    with tabs[4]:
        terms = load_csv_safe(str(NLP_DIR / "outputs/top_terms.csv"))
        if terms.empty:
            empty_state_panel(t("nlp_term_report_missing"), t("nlp_terms_missing"))
        else:
            left, right = st.columns(2)
            with left:
                section_heading(t("nlp_positive_terms"))
                metric_table(terms[terms["sentiment"] == "positive"] if "sentiment" in terms else terms.head(30))
            with right:
                section_heading(t("nlp_negative_terms"))
                metric_table(terms[terms["sentiment"] == "negative"] if "sentiment" in terms else terms.tail(30))
        st.caption(t("nlp_terms_note"))
    with tabs[5]:
        metric_table(load_csv_safe(str(NLP_DIR / "outputs/error_analysis.csv")), t("nlp_error_report_missing"))
    with tabs[6]:
        source = load_text_safe(str(NLP_DIR / "DATA_SOURCE.md"))
        st.markdown(source) if source else empty_state_panel(t("nlp_source_missing"), t("nlp_data_source_missing"))

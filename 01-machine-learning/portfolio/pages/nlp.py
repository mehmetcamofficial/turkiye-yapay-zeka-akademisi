from __future__ import annotations
from html import escape

import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from portfolio.config import NLP_DIR, NLP_MODEL_PATH
from portfolio.experiment_store import normalize_gridsearch_results, record_gridsearch_experiment
from portfolio.i18n import t
from portfolio.loaders import (load_csv_safe, load_image_path_safe,
                               load_json_safe, load_model_safe, load_text_safe)
from portfolio.project_registry import project_by_id
from portfolio.ui_components import (artifact_checklist, classification_report_frame, empty_state_panel,
                                     hero_panel, information_panel, log_activity,
                                     metric_table, prediction_result_card, render_safe_table, section_heading)


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


def _confidence_gauge(prob: float) -> None:
    color = "#22c55e" if prob >= 0.8 else ("#f59e0b" if prob >= 0.6 else "#ef4444")
    fig, ax = plt.subplots(figsize=(6, 0.5))
    ax.barh([""], [prob], color=color, height=0.4)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7)
    ax.axvline(0.6, color="#94a3b8", linestyle="--", linewidth=0.5)
    ax.axvline(0.8, color="#94a3b8", linestyle="--", linewidth=0.5)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    st.pyplot(fig)


def _term_influence(text: str, terms_df: pd.DataFrame) -> None:
    words = _clean_text(text).split()
    if not words or terms_df.empty:
        return
    if "sentiment" not in terms_df or "weight" not in terms_df or "term" not in terms_df:
        return
    word_matches = terms_df[terms_df["term"].isin(words)].copy()
    if word_matches.empty:
        st.caption(t("nlp_no_matched_terms"))
        return
    fig, ax = plt.subplots(figsize=(6, max(1.5, len(word_matches) * 0.3)))
    colors = ["#22c55e" if r["sentiment"] == "positive" else "#ef4444" for _, r in word_matches.iterrows()]
    sorted_matches = word_matches.sort_values("weight")
    ax.barh(sorted_matches["term"], sorted_matches["weight"], color=colors, height=0.5)
    ax.axvline(0, color="#64748b", linewidth=0.5)
    ax.set_xlabel(t("weight"))
    ax.set_title(t("nlp_matched_terms"), fontsize=10)
    fig.tight_layout()
    st.pyplot(fig)


def _single() -> None:
    model_result = _model()
    text = st.text_area(t("nlp_text_input"), "This product works perfectly and I love it.", height=130)
    if st.button(t("nlp_analyze"), key="nlp_single_predict", type="primary"):
        if not model_result.ok:
            st.error(model_result.public_message); return
        model = model_result.model
        prepared = [_clean_text(text)]
        if not prepared[0]:
            st.warning(t("nlp_empty_text")); return
        try:
            label = int(model.predict(prepared)[0]); scores = _confidence(model, prepared)
            sentiment_label = t("nlp_positive") if label == 1 else t("nlp_negative")
            sentiment_color = "#22c55e" if label == 1 else "#ef4444"
            st.markdown(f"**{escape(t('nlp_predicted'))}**")
            st.markdown(
                f'<p style="font-size:2rem;font-weight:700;color:{sentiment_color};'
                f"margin:0 0 8px 0;\">{escape(sentiment_label)}</p>",
                unsafe_allow_html=True,
            )
            if scores is not None:
                proba = model.predict_proba(prepared)[0]
                pos_prob = float(proba[1])
                neg_prob_val = float(proba[0])
                col1, col2 = st.columns(2)
                col1.metric(t("nlp_positive_prob"), f"%{pos_prob*100:.1f}",
                            help=t("nlp_binary_note"))
                col2.metric(t("nlp_negative_prob"), f"%{neg_prob_val*100:.1f}",
                            help=t("nlp_binary_note"))
                bar_html = (
                    f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;margin:4px 0;">'
                    f'<div style="flex:{pos_prob:.3f};background:#22c55e;"></div>'
                    f'<div style="flex:{neg_prob_val:.3f};background:#ef4444;"></div>'
                    f'</div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:0.7rem;">'
                    f'<span style="color:#22c55e;">{t("nlp_positive")} %{pos_prob*100:.1f}</span>'
                    f'<span style="color:#ef4444;">{t("nlp_negative")} %{neg_prob_val*100:.1f}</span>'
                    f'</div>'
                )
                st.markdown(bar_html, unsafe_allow_html=True)
            else:
                st.caption(t("nlp_binary_note"))
            terms = load_csv_safe(str(NLP_DIR / "outputs/top_terms.csv"))
            if not terms.empty:
                _term_influence(text, terms)
                st.caption(t("nlp_term_influence_note"))
            log_activity(t("ml_section_nlp"), t("activity_prediction_completed"))
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
        gs_raw = load_csv_safe(str(NLP_DIR / "outputs/hyperparameter_search_results.csv"))
        gs_df = normalize_gridsearch_results(gs_raw) if not gs_raw.empty else gs_raw
        if not gs_df.empty:
            render_safe_table(gs_df)
            record_gridsearch_experiment(
                capability=t("ml_section_nlp"),
                model_name="MultinomialNB",
                source_dir=str(NLP_DIR / "outputs/hyperparameter_search_results.csv"),
                notes="NLP GridSearchCV results viewed",
            )
        else:
            empty_state_panel(t("nlp_gridsearch"), t("nlp_tuning_missing"))
    report = load_text_safe(str(NLP_DIR / "outputs/classification_report.txt"))
    if report: metric_table(classification_report_frame(report))
    image = load_image_path_safe(str(NLP_DIR / "outputs/confusion_matrix.png"))
    if image: st.image(image, use_column_width=True)
    terms = load_csv_safe(str(NLP_DIR / "outputs/top_terms.csv"))
    if not terms.empty and "sentiment" in terms and "weight" in terms:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5))
        pos = terms[terms["sentiment"] == "positive"].head(10)
        neg = terms[terms["sentiment"] == "negative"].head(10)
        ax1.barh(pos["term"].iloc[::-1], pos["weight"].iloc[::-1], color="#22c55e", height=0.6)
        ax1.set_title(t("nlp_top_positive"), fontsize=10)
        ax1.set_xlabel(t("weight"))
        ax2.barh(neg["term"].iloc[::-1], neg["weight"].iloc[::-1], color="#ef4444", height=0.6)
        ax2.set_title(t("nlp_top_negative"), fontsize=10)
        ax2.set_xlabel(t("weight"))
        fig.tight_layout()
        st.pyplot(fig)


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
            column.metric(name, t("metric_not_calculated") if value is None else f"{value:.4f}")
        information_panel(t("purpose"), project["description"])
        information_panel(t("data_model"), f"{project['dataset']} ({project['dataset_size']}) · {project['final_model']}")
        information_panel(t("workflow"), t("nlp_workflow_desc"))
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

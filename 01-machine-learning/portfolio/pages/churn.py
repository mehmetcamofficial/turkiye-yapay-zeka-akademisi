"""Native unified-portfolio UI for the existing churn pipeline."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from portfolio.churn_service import (RAW_COLUMNS, predict_batch, prepare_model_input,
                                     sample_batch, validate_raw_batch)
from portfolio.config import CHURN_DIR, CHURN_MODEL_PATH
from portfolio.i18n import t
from portfolio.loaders import (load_csv_safe, load_image_path_safe,
                               load_json_safe, load_model_safe, load_text_safe)
from portfolio.project_registry import project_by_id
from portfolio.ui_components import (artifact_checklist, classification_report_frame, empty_state_panel,
                                     hero_panel, information_panel, metric_table,
                                     prediction_result_card, render_safe_table, section_heading)


def _model_result():
    return load_model_safe(CHURN_MODEL_PATH)


def _single_prediction() -> None:
    model_result = _model_result()
    if not model_result.ok:
        empty_state_panel(t("churn_model_unavail"), model_result.public_message)
        return
    with st.form("portfolio_churn_single"):
        left, right = st.columns(2)
        with left:
            gender = st.selectbox(t("gender"), ["Female", "Male"])
            senior = st.selectbox(t("senior_citizen"), ["No", "Yes"])
            partner = st.selectbox(t("partner"), ["No", "Yes"])
            dependents = st.selectbox(t("dependents"), ["No", "Yes"])
            tenure = st.number_input(t("tenure_months"), min_value=0, max_value=120, value=12)
            phone = st.selectbox(t("phone_service"), ["Yes", "No"])
            multiple = st.selectbox(t("multiple_lines"), ["No", "Yes", "No phone service"])
            internet = st.selectbox(t("internet_service"), ["Fiber optic", "DSL", "No"])
            security = st.selectbox(t("online_security"), ["No", "Yes", "No internet service"])
            backup = st.selectbox(t("online_backup"), ["No", "Yes", "No internet service"])
        with right:
            protection = st.selectbox(t("device_protection"), ["No", "Yes", "No internet service"])
            support = st.selectbox(t("tech_support"), ["No", "Yes", "No internet service"])
            tv = st.selectbox(t("streaming_tv"), ["No", "Yes", "No internet service"])
            movies = st.selectbox(t("streaming_movies"), ["No", "Yes", "No internet service"])
            contract = st.selectbox(t("contract"), ["Month-to-month", "One year", "Two year"])
            paperless = st.selectbox(t("paperless_billing"), ["Yes", "No"])
            payment = st.selectbox(t("payment_method"), ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"])
            monthly = st.number_input(t("monthly_charges"), min_value=0.0, value=75.0)
            total = st.number_input(t("total_charges"), min_value=0.0, value=900.0)
            cltv = st.number_input(t("cltv"), min_value=0.0, value=3500.0)
        submitted = st.form_submit_button(t("churn_risk_calc"))
    if submitted:
        raw = pd.DataFrame([dict(zip(RAW_COLUMNS, [gender, senior, partner, dependents, tenure, phone, multiple,
            internet, security, backup, protection, support, tv, movies, contract, paperless, payment,
            monthly, total, cltv]))])
        try:
            prepared = prepare_model_input(raw)
            prediction = int(model_result.model.predict(prepared)[0])
            probability = float(model_result.model.predict_proba(prepared)[0, 1])
            risk = t("churn_risk_high") if probability >= .7 else (t("churn_risk_medium") if probability >= .4 else t("churn_risk_low"))
            prediction_result_card(t("churn_prediction"), t("churn_risk_high") if prediction else t("churn_risk_low"),
                                   t("churn_prob", prob=probability, risk=risk))
        except Exception:
            st.error(t("churn_pred_failed"))


def _read_uploaded_csv(uploaded) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(uploaded)
        if len(frame.columns) == 1:
            uploaded.seek(0)
            alternate = pd.read_csv(uploaded, sep=";")
            if len(alternate.columns) > 1:
                frame = alternate
        return frame
    except (UnicodeError, pd.errors.ParserError, ValueError):
        st.error(t("churn_csv_error"))
        return None


def _batch_prediction() -> None:
    template = sample_batch()
    st.download_button(t("churn_download_template"), template.to_csv(index=False).encode("utf-8"),
                       "churn_batch_template.csv", "text/csv")
    uploaded = st.file_uploader(t("churn_upload_csv"), type="csv", key="portfolio_churn_batch")
    if uploaded is None:
        information_panel(t("churn_batch_pred"), t("churn_batch_desc"))
        return
    frame = _read_uploaded_csv(uploaded)
    if frame is None:
        return
    errors = validate_raw_batch(frame)
    if errors:
        for error in errors: st.warning(error)
        return
    st.caption(t("churn_records_validated", count=len(frame)))
    render_safe_table(frame, max_rows=25)
    if st.button(t("churn_run_batch"), key="portfolio_churn_batch_run"):
        model_result = _model_result()
        if not model_result.ok:
            st.error(model_result.public_message); return
        try:
            result = predict_batch(model_result.model, frame)
            st.session_state["churn_batch_result"] = result
        except Exception:
            st.error(t("churn_batch_failed"))
    result = st.session_state.get("churn_batch_result")
    if isinstance(result, pd.DataFrame):
        render_safe_table(result, max_rows=100, download_name=None)
        high_risk = result[result["Risk Band"] == t("churn_risk_high")]
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(t("churn_download_all"), result.to_csv(index=False).encode("utf-8"), "churn_predictions.csv", "text/csv")
        with col2:
            st.download_button(t("churn_download_high"), high_risk.to_csv(index=False).encode("utf-8"), "high_risk_customers.csv", "text/csv")
        st.caption(t("churn_high_risk", count=len(high_risk)))
        if "Risk Band" in result.columns:
            fig, ax = plt.subplots(figsize=(5, 2))
            risk_counts = result["Risk Band"].value_counts()
            colors = {"Yüksek Risk": "#ef4444", "Orta Risk": "#eab308", "Düşük Risk": "#22c55e"}
            bar_colors = [colors.get(r, "#94a3b8") for r in risk_counts.index]
            ax.bar(risk_counts.index, risk_counts.values, color=bar_colors, width=0.5)
            for i, v in enumerate(risk_counts.values):
                ax.text(i, v + 0.1, str(v), ha="center", fontsize=9)
            ax.set_title(t("risk_distribution"), fontsize=10)
            ax.tick_params(axis="x", rotation=30)
            fig.tight_layout()
            st.pyplot(fig)


def _performance() -> None:
    reports = [(t("churn_final_metrics"), "test_metrics.csv"), (t("churn_validation"), "validation_results.csv"),
               (t("churn_cv"), "cross_validation_results.csv"), (t("churn_gridsearch"), "hyperparameter_search_results.csv")]
    for title, filename in reports:
        section_heading(title); metric_table(load_csv_safe(str(CHURN_DIR / "outputs" / filename)))
    section_heading(t("churn_best_params"))
    params = load_json_safe(str(CHURN_DIR / "outputs/best_hyperparameters.json"))
    if params: st.json(params)
    else: empty_state_panel(t("churn_report_missing"), t("churn_json_missing"))
    report = load_text_safe(str(CHURN_DIR / "outputs/classification_report.txt"))
    if report:
        section_heading(t("churn_class_report"), t("churn_class_desc"))
        metric_table(classification_report_frame(report))
    columns = st.columns(2)
    for column, filename, title in [(columns[0], "confusion_matrix.png", t("churn_confusion")), (columns[1], "roc_curve.png", t("churn_roc"))]:
        with column:
            image = load_image_path_safe(str(CHURN_DIR / "outputs" / filename))
            if image: st.image(image, caption=title, use_column_width=True)


def _explainability() -> None:
    section_heading(t("churn_selected_features"))
    selected = load_csv_safe(str(CHURN_DIR / "outputs/selected_features.csv"))
    if "selected" in selected: selected = selected[selected["selected"] == True]  # noqa: E712
    metric_table(selected)
    section_heading(t("churn_coeff"))
    metric_table(load_csv_safe(str(CHURN_DIR / "outputs/feature_importance.csv")))
    st.caption(t("churn_coeff_note"))


def render() -> None:
    hero_panel(
        title=t("ml_section_churn"),
        subtitle=t("subtitle_churn"),
        kicker=t("section_ml"),
    )
    tabs = st.tabs([t("tab_overview"), t("tab_single_prediction"), t("tab_batch_csv"), t("tab_model_performance"), t("tab_explainability"), t("tab_methodology"), t("tab_technical")])
    project = project_by_id("churn")
    with tabs[0]:
        metrics = load_csv_safe(str(CHURN_DIR / "outputs/test_metrics.csv"))
        columns = st.columns(4)
        for column, name in zip(columns, ["Accuracy", "Recall", "F1 Score", "ROC AUC"]):
            value = float(metrics.iloc[0][name]) if not metrics.empty and name in metrics else None
            column.metric(name, "—" if value is None else f"{value:.4f}")
        fig, ax = plt.subplots(figsize=(5, 2))
        names = ["Accuracy", "Recall", "F1 Score", "ROC AUC"]
        vals = [float(metrics.iloc[0][n]) if not metrics.empty and n in metrics else 0 for n in names]
        bars = ax.bar(names, vals, color=["#6366f1", "#22c55e", "#eab308", "#ef4444"], width=0.5)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{v:.4f}", ha="center", fontsize=8)
        ax.set_ylim(0, 1.0)
        ax.set_title(t("model_performance"), fontsize=10)
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        st.pyplot(fig)
        information_panel(t("purpose"), project["description"])
        information_panel(t("data_model"), f"{project['dataset']} ({project['dataset_size']}) · {project['final_model']}")
        information_panel(t("workflow"), "EDA → feature engineering → preprocessing → feature selection → 5-fold CV → tuning → untouched test")
        information_panel(t("limitations"), "; ".join(project["limitations"]))
    with tabs[1]: _single_prediction()
    with tabs[2]: _batch_prediction()
    with tabs[3]: _performance()
    with tabs[4]: _explainability()
    with tabs[5]:
        information_panel(t("churn_preprocessing"), t("churn_preprocessing_desc"))
        information_panel(t("churn_model_selection"), t("churn_model_selection_desc"))
    with tabs[6]:
        with st.expander(t("churn_artifact_checklist"), expanded=False): artifact_checklist(project)
        with st.expander(t("churn_final_report"), expanded=False):
            summary = load_text_safe(str(CHURN_DIR / "outputs/final_summary.txt"))
            st.text(summary) if summary else st.info(t("churn_final_report_missing"))

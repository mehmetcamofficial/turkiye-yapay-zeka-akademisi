from __future__ import annotations
from html import escape

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from portfolio.churn_service import (
    MODEL_COLUMNS,
    RAW_COLUMNS,
    prepare_model_input,
    sample_batch,
    validate_raw_batch,
    predict_batch,
)
from portfolio.config import CHURN_DIR, CHURN_MODEL_PATH
from portfolio.i18n import t
from portfolio.loaders import (
    load_csv_safe,
    load_image_path_safe,
    load_json_safe,
    load_model_safe,
    load_text_safe,
)
from portfolio.project_registry import project_by_id
from portfolio.ui_components import (
    artifact_checklist,
    classification_report_frame,
    empty_state_panel,
    hero_panel,
    information_panel,
    metric_table,
    prediction_result_card,
    render_safe_table,
    section_heading,
)

LOW_RISK = ["Female", "No", "Yes", "No", 12, "Yes", "No", "Fiber optic",
            "No", "Yes", "No", "No", "Yes", "Yes", "Month-to-month", "Yes",
            "Electronic check", 89.5, 1074.0, 3200.0]
HIGH_RISK = ["Male", "Yes", "No", "No", 2, "Yes", "Yes", "Fiber optic",
             "No", "No", "No", "No", "No", "No", "Month-to-month", "Yes",
             "Electronic check", 120.0, 240.0, 1800.0]


def _model_result():
    return load_model_safe(CHURN_MODEL_PATH)


def _single_prediction() -> None:
    model_result = _model_result()
    if not model_result.ok:
        empty_state_panel(t("churn_model_unavail"), model_result.public_message)
        return

    st.markdown(f"**{t('preset_scenarios')}**")
    preset_left, preset_right = st.columns(2)
    with preset_left:
        use_low = st.button(t("low_risk_preset"), key="churn_low_preset", type="secondary")
    with preset_right:
        use_high = st.button(t("high_risk_preset"), key="churn_high_preset", type="secondary")

    preselected = LOW_RISK if use_low else (HIGH_RISK if use_high else None)

    with st.form("portfolio_churn_single"):
        left, right = st.columns(2)
        with left:
            gender = st.selectbox(t("gender"), ["Female", "Male"], index=0 if preselected is None else 0 if preselected[0] == "Female" else 1)
            senior = st.selectbox(t("senior_citizen"), ["No", "Yes"], index=0 if preselected is None else 0 if preselected[1] == "No" else 1)
            partner = st.selectbox(t("partner"), ["No", "Yes"], index=0 if preselected is None else 0 if preselected[2] == "No" else 1)
            dependents = st.selectbox(t("dependents"), ["No", "Yes"], index=0 if preselected is None else 0 if preselected[3] == "No" else 1)
            tenure = st.number_input(t("tenure_months"), min_value=0, max_value=120, value=12 if preselected is None else preselected[4])
            phone = st.selectbox(t("phone_service"), ["Yes", "No"], index=0 if preselected is None else 0 if preselected[5] == "Yes" else 1)
            multiple = st.selectbox(t("multiple_lines"), ["No", "Yes", "No phone service"], index=0 if preselected is None else ["No", "Yes", "No phone service"].index(preselected[6]))
            internet = st.selectbox(t("internet_service"), ["Fiber optic", "DSL", "No"], index=0 if preselected is None else ["Fiber optic", "DSL", "No"].index(preselected[7]))
            security = st.selectbox(t("online_security"), ["No", "Yes", "No internet service"], index=0 if preselected is None else ["No", "Yes", "No internet service"].index(preselected[8]))
            backup = st.selectbox(t("online_backup"), ["No", "Yes", "No internet service"], index=0 if preselected is None else ["No", "Yes", "No internet service"].index(preselected[9]))
        with right:
            protection = st.selectbox(t("device_protection"), ["No", "Yes", "No internet service"], index=0 if preselected is None else ["No", "Yes", "No internet service"].index(preselected[10]))
            support = st.selectbox(t("tech_support"), ["No", "Yes", "No internet service"], index=0 if preselected is None else ["No", "Yes", "No internet service"].index(preselected[11]))
            tv = st.selectbox(t("streaming_tv"), ["No", "Yes", "No internet service"], index=0 if preselected is None else ["No", "Yes", "No internet service"].index(preselected[12]))
            movies = st.selectbox(t("streaming_movies"), ["No", "Yes", "No internet service"], index=0 if preselected is None else ["No", "Yes", "No internet service"].index(preselected[13]))
            contract = st.selectbox(t("contract"), ["Month-to-month", "One year", "Two year"], index=0 if preselected is None else ["Month-to-month", "One year", "Two year"].index(preselected[14]))
            paperless = st.selectbox(t("paperless_billing"), ["Yes", "No"], index=0 if preselected is None else 0 if preselected[15] == "Yes" else 1)
            payment = st.selectbox(t("payment_method"), ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"], index=0 if preselected is None else ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"].index(preselected[16]))
            monthly = st.number_input(t("monthly_charges"), min_value=0.0, value=75.0 if preselected is None else preselected[17])
            total = st.number_input(t("total_charges"), min_value=0.0, value=900.0 if preselected is None else preselected[18])
            cltv = st.number_input(t("cltv"), min_value=0.0, value=3500.0 if preselected is None else preselected[19])
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
            st.markdown(
                f'<div class="prediction-card">'
                f"<strong>{escape(t('churn_prediction'))}</strong>"
                f"<span>{escape(t('churn_risk_high') if prediction else t('churn_risk_low'))}</span>"
                f"<small>{escape(t('churn_prob', prob=probability, risk=risk))}</small>"
                f"</div>",
                unsafe_allow_html=True,
            )
            fig, ax = plt.subplots(figsize=(6, 0.6))
            ax.barh([""], [probability], color="#ef4444" if probability >= 0.7 else ("#f59e0b" if probability >= 0.4 else "#22c55e"), height=0.4)
            ax.set_xlim(0, 1)
            ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
            ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7)
            ax.axvline(0.4, color="#94a3b8", linestyle="--", linewidth=0.5)
            ax.axvline(0.7, color="#94a3b8", linestyle="--", linewidth=0.5)
            ax.tick_params(axis="y", length=0)
            fig.tight_layout()
            st.pyplot(fig)
            st.caption(t("churn_prob_scale"))
        except Exception:
            st.error(t("churn_pred_failed"))


def _batch_prediction() -> None:
    model_result = _model_result()
    uploaded = st.file_uploader(t("churn_upload_csv"), type="csv", key="churn_batch")
    if uploaded is None:
        sample = sample_batch()
        if st.button(t("churn_download_template")):
            st.download_button(t("churn_download_template"), sample.to_csv(index=False).encode("utf-8"),
                               "churn_sample.csv", "text/csv")
        information_panel(t("churn_batch_pred"), t("churn_batch_desc"))
        return
    try:
        frame = pd.read_csv(uploaded)
    except (UnicodeError, pd.errors.ParserError):
        st.error(t("churn_csv_error")); return
    errors = validate_raw_batch(frame)
    if errors:
        for e in errors: st.error(e); return
    if not model_result.ok:
        st.error(model_result.public_message); return
    if st.button(t("churn_run_batch"), key="churn_batch"):
        try:
            result = predict_batch(model_result.model, frame)
            high_count = int(result["Risk Band"].eq("Yüksek").sum())
            render_safe_table(result, max_rows=100)
            st.download_button(t("churn_download_all"), result.to_csv(index=False).encode("utf-8"),
                               "churn_predictions.csv", "text/csv")
            if high_count:
                high_risk = result[result["Risk Band"] == "Yüksek"]
                st.download_button(t("churn_download_high"), high_risk.to_csv(index=False).encode("utf-8"),
                                   "churn_high_risk.csv", "text/csv")
                st.warning(t("churn_high_risk", count=high_count))
        except Exception:
            st.error(t("churn_batch_failed"))


def _performance() -> None:
    section_heading(t("churn_final_metrics"))
    metric_table(load_csv_safe(str(CHURN_DIR / "outputs/test_metrics.csv")))
    section_heading(t("churn_validation"))
    metric_table(load_csv_safe(str(CHURN_DIR / "outputs/validation_results.csv")))
    section_heading(t("churn_cv"))
    metric_table(load_csv_safe(str(CHURN_DIR / "outputs/cross_validation_results.csv")))
    report = load_text_safe(str(CHURN_DIR / "outputs/classification_report.txt"))
    if report:
        section_heading(t("churn_class_report"), t("churn_class_desc"))
        metric_table(classification_report_frame(report))
    image = load_image_path_safe(str(CHURN_DIR / "outputs/confusion_matrix.png"))
    if image: st.image(image, use_column_width=True)


def _coefficients() -> None:
    section_heading(t("churn_selected_features"))
    metric_table(load_csv_safe(str(CHURN_DIR / "outputs/selected_features.csv")))
    section_heading(t("churn_coeff"))
    coef = load_csv_safe(str(CHURN_DIR / "outputs/feature_importance.csv"))
    if not coef.empty:
        col_name = [c for c in coef if "coef" in c.lower() or "importance" in c.lower()]
        coef_col = col_name[0] if col_name else coef.columns[-1]
        feature_col = [c for c in coef if "feature" in c.lower() or c == "feature" or c == "Variable"]
        feat_col = feature_col[0] if feature_col else coef.columns[0]
        coef["abs"] = coef[coef_col].abs()
        top = coef.nlargest(15, "abs")[[feat_col, coef_col]]
        top.columns = [t("feature"), t("coefficient")]
        render_safe_table(top, max_rows=15)
    st.caption(t("churn_coeff_note"))
    section_heading(t("churn_best_params"))
    payload = load_json_safe(str(CHURN_DIR / "outputs/best_hyperparameters.json"))
    st.json(payload) if payload else empty_state_panel(t("churn_json_missing"), t("churn_json_missing"))
    with st.expander(t("churn_gridsearch"), expanded=False):
        metric_table(load_csv_safe(str(CHURN_DIR / "outputs/hyperparameter_search_results.csv")))
    section_heading(t("churn_preprocessing"), t("churn_preprocessing_desc"))
    section_heading(t("churn_model_selection"), t("churn_model_selection_desc"))


def _roc_curve() -> None:
    image = load_image_path_safe(str(CHURN_DIR / "outputs/roc_curve.png"))
    if image:
        st.image(image, use_column_width=True)
    else:
        empty_state_panel(t("churn_report_missing"), t("churn_roc"))
    with st.expander(t("churn_final_report"), expanded=False):
        report = load_text_safe(str(CHURN_DIR / "outputs/final_report.md"))
        if report: st.markdown(report)


def render() -> None:
    hero_panel(
        title=t("ml_section_churn"),
        subtitle=t("subtitle_churn"),
        kicker=t("section_ml"),
    )
    tabs = st.tabs([t("tab_overview"), t("tab_single_prediction"), t("tab_batch_prediction"), t("tab_model_performance"), t("tab_explainability"), t("tab_roc_curve")])
    with tabs[0]:
        project = project_by_id("churn")
        metrics = load_csv_safe(str(CHURN_DIR / "outputs/test_metrics.csv"))
        columns = st.columns(4)
        for column, name in zip(columns, ["Accuracy", "Recall", "F1", "ROC AUC"]):
            value = float(metrics.iloc[0][name]) if not metrics.empty and name in metrics else None
            column.metric(name, "—" if value is None else f"{value:.4f}")
        information_panel(t("purpose"), project["description"])
        information_panel(t("data_model"), f"{project['dataset']} ({project['dataset_size']}) · {project['final_model']}")
        information_panel(t("workflow"), t("churn_workflow_desc"))
        information_panel(t("limitations"), "; ".join(project["limitations"]))
        with st.expander(t("tab_technical"), expanded=False):
            artifact_checklist(project)
    with tabs[1]: _single_prediction()
    with tabs[2]: _batch_prediction()
    with tabs[3]: _performance()
    with tabs[4]: _coefficients()
    with tabs[5]: _roc_curve()

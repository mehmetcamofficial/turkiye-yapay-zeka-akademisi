"""Fully integrated California Housing regression module."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from portfolio.config import REGRESSION_DIR, REGRESSION_MODEL_PATH
from portfolio.i18n import t
from portfolio.loaders import (load_csv_safe, load_image_path_safe,
                               load_json_safe, load_model_safe, load_text_safe)
from portfolio.project_registry import project_by_id
from portfolio.ui_components import (artifact_checklist, empty_state_panel,
                                     hero_panel, information_panel, metric_table,
                                     prediction_result_card, render_safe_table, section_heading)

RAW_COLUMNS = ["MedInc", "HouseAge", "AveRooms", "AveBedrms", "Population", "AveOccup", "Latitude", "Longitude"]


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in RAW_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result["RoomsPerBedroom"] = result["AveRooms"] / result["AveBedrms"].replace(0, np.nan)
    result["BedroomsPerOccupant"] = result["AveBedrms"] / result["AveOccup"].replace(0, np.nan)
    return result


def _model():
    return load_model_safe(REGRESSION_MODEL_PATH)


def _single_prediction() -> None:
    model_result = _model()
    if not model_result.ok:
        empty_state_panel(t("regression_model_unavail"), model_result.public_message)
        return
    model = model_result.model
    defaults = [3.87, 28.6, 5.43, 1.10, 1425.0, 3.07, 35.63, -119.57]
    with st.form("regression_single_form"):
        columns = st.columns(2); values = {}
        for index, (name, default) in enumerate(zip(RAW_COLUMNS, defaults)):
            values[name] = columns[index % 2].number_input(name, value=float(default), format="%.4f")
        submitted = st.form_submit_button(t("regression_predict"))
    if submitted:
        try:
            prediction = float(model.predict(_prepare(pd.DataFrame([values])))[0])
            prediction_result_card(t("regression_pred_value"),
                                   f"${prediction * 100_000:,.0f}",
                                   t("regression_pred_desc", pred=prediction))
        except Exception:
            st.error(t("regression_pred_failed"))


def _batch_prediction() -> None:
    model_result = _model()
    uploaded = st.file_uploader(t("regression_upload_csv"), type="csv", key="regression_batch")
    if uploaded is None:
        information_panel(t("regression_expected_cols"), ", ".join(RAW_COLUMNS))
        return
    try:
        frame = pd.read_csv(uploaded)
    except (UnicodeError, pd.errors.ParserError):
        st.error(t("regression_csv_error")); return
    missing = [column for column in RAW_COLUMNS if column not in frame]
    if missing:
        st.error(t("regression_missing_cols", cols=", ".join(missing))); return
    if not model_result.ok:
        st.error(model_result.public_message); return
    model = model_result.model
    try:
        result = frame.copy()
        result["PredictedValue100kUSD"] = model.predict(_prepare(frame[RAW_COLUMNS]))
        result["PredictedValueUSD"] = result["PredictedValue100kUSD"] * 100_000
        render_safe_table(result, max_rows=100)
        st.download_button(t("regression_download_pred"), result.to_csv(index=False).encode("utf-8"),
                           "california_housing_predictions.csv", "text/csv")
    except Exception:
        st.error(t("regression_batch_failed"))


def _performance() -> None:
    section_heading(t("regression_final_metrics"))
    metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/test_metrics.csv")))
    section_heading(t("regression_validation"))
    metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/validation_results.csv")))
    section_heading(t("regression_cv"))
    metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/cross_validation_results.csv")))
    section_heading(t("regression_best_params"))
    payload = load_json_safe(str(REGRESSION_DIR / "outputs/best_hyperparameters.json"))
    st.json(payload) if payload else empty_state_panel(t("regression_json_missing"), t("regression_hparam_missing"))
    with st.expander(t("regression_gridsearch"), expanded=False):
        metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/hyperparameter_search_results.csv")))
    section_heading(t("regression_feature_imp"))
    metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/feature_importance.csv")))


def _residuals() -> None:
    section_heading(t("regression_pred_vs_actual"), t("regression_pred_actual_desc"))
    model_result = _model()
    if model_result.ok:
        try:
            import sklearn.datasets
            housing = sklearn.datasets.fetch_california_housing()
            X = pd.DataFrame(housing.data, columns=housing.feature_names)
            X.columns = RAW_COLUMNS
            y_true = housing.target
            y_pred = model_result.model.predict(_prepare(X))
            residuals = y_true - y_pred
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5))
            ax1.scatter(y_true, y_pred, alpha=0.3, s=8, color="#6366f1")
            min_val = min(y_true.min(), y_pred.min())
            max_val = max(y_true.max(), y_pred.max())
            ax1.plot([min_val, max_val], [min_val, max_val], "r--", linewidth=0.8)
            ax1.set_xlabel(t("actual_values"))
            ax1.set_ylabel(t("predicted_values"))
            ax1.set_title(t("pred_vs_actual"), fontsize=10)
            ax2.hist(residuals, bins=40, color="#6366f1", edgecolor="white")
            ax2.axvline(0, color="#ef4444", linestyle="--", linewidth=0.8)
            ax2.set_xlabel(t("residual"))
            ax2.set_ylabel(t("frequency"))
            ax2.set_title(t("residual_distribution"), fontsize=10)
            fig.tight_layout()
            st.pyplot(fig)
        except Exception:
            pass
    columns = st.columns(2)
    for column, filename, title in [(columns[0], "residual_plot.png", t("regression_residuals")),
                                     (columns[1], "prediction_vs_actual.png", t("regression_pred_vs_actual"))]:
        with column:
            image = load_image_path_safe(str(REGRESSION_DIR / "outputs" / filename))
            if image: st.image(image, use_column_width=True)


def render() -> None:
    hero_panel(
        title=t("ml_section_housing"),
        subtitle=t("subtitle_regression"),
        kicker=t("section_ml"),
    )
    tabs = st.tabs([t("tab_overview"), t("tab_single_prediction"), t("tab_batch_prediction"), t("tab_model_performance"), t("tab_residuals"), t("tab_data_source")])
    with tabs[0]:
        project = project_by_id("regression")
        metrics = load_csv_safe(str(REGRESSION_DIR / "outputs/test_metrics.csv"))
        columns = st.columns(3)
        for column, name in zip(columns, ["RMSE", "MAE", "R2"]):
            value = float(metrics.iloc[0][name]) if not metrics.empty and name in metrics else None
            column.metric(name, "—" if value is None else f"{value:.4f}")
        information_panel(t("purpose"), project["description"])
        information_panel(t("data_model"), f"{project['dataset']} ({project['dataset_size']}) · {project['final_model']}")
        information_panel(t("workflow"), "Yerel veri → EDA → hedef-bağımsız oranlar → preprocessing → SelectKBest → 5-fold CV → tuning → test")
        information_panel(t("limitations"), "; ".join(project["limitations"]))
        with st.expander(t("tab_technical"), expanded=False):
            artifact_checklist(project)
    with tabs[1]: _single_prediction()
    with tabs[2]: _batch_prediction()
    with tabs[3]: _performance()
    with tabs[4]: _residuals()
    with tabs[5]:
        source = load_text_safe(str(REGRESSION_DIR / "DATA_SOURCE.md"))
        st.markdown(source) if source else empty_state_panel(t("regression_data_missing"), t("regression_data_not_found"))

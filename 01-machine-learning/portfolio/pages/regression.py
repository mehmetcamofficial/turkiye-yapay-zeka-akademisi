"""Fully integrated California Housing regression module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from portfolio.config import REGRESSION_DIR, REGRESSION_MODEL_PATH
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
        empty_state_panel("Model kullanılamıyor", model_result.public_message)
        return
    model = model_result.model
    defaults = [3.87, 28.6, 5.43, 1.10, 1425.0, 3.07, 35.63, -119.57]
    with st.form("regression_single_form"):
        columns = st.columns(2); values = {}
        for index, (name, default) in enumerate(zip(RAW_COLUMNS, defaults)):
            values[name] = columns[index % 2].number_input(name, value=float(default), format="%.4f")
        submitted = st.form_submit_button("Tahmin Oluştur")
    if submitted:
        try:
            prediction = float(model.predict(_prepare(pd.DataFrame([values])))[0])
            prediction_result_card("Tahmini medyan bölge ev değeri", f"${prediction * 100_000:,.0f}",
                                   f"Model hedefi {prediction:.4f} (100.000 USD birimi). Eğitim amaçlı model tahminidir; ekspertiz değeri değildir.")
        except Exception:
            st.error("Tahmin oluşturulamadı. Girdi değerlerini kontrol edin.")


def _batch_prediction() -> None:
    model_result = _model()
    uploaded = st.file_uploader("Sekiz California Housing özelliğini içeren CSV yükleyin", type="csv", key="regression_batch")
    if uploaded is None:
        information_panel("Beklenen sütunlar", ", ".join(RAW_COLUMNS))
        return
    try:
        frame = pd.read_csv(uploaded)
    except (UnicodeError, pd.errors.ParserError):
        st.error("CSV okunamadı. Dosya kodlamasını ve ayırıcısını kontrol edin."); return
    missing = [column for column in RAW_COLUMNS if column not in frame]
    if missing:
        st.error("Eksik sütunlar: " + ", ".join(missing)); return
    if not model_result.ok:
        st.error(model_result.public_message); return
    model = model_result.model
    try:
        result = frame.copy()
        result["PredictedValue100kUSD"] = model.predict(_prepare(frame[RAW_COLUMNS]))
        result["PredictedValueUSD"] = result["PredictedValue100kUSD"] * 100_000
        render_safe_table(result, max_rows=100)
        st.download_button("Tahminleri CSV olarak indir", result.to_csv(index=False).encode("utf-8"),
                           "california_housing_predictions.csv", "text/csv")
    except Exception:
        st.error("Toplu tahmin tamamlanamadı. Sayısal alanları kontrol edin.")


def _performance() -> None:
    section_heading("Final test metrikleri")
    metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/test_metrics.csv")))
    section_heading("Validation karşılaştırması")
    metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/validation_results.csv")))
    section_heading("5-fold cross-validation")
    metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/cross_validation_results.csv")))
    section_heading("En iyi hiperparametreler")
    payload = load_json_safe(str(REGRESSION_DIR / "outputs/best_hyperparameters.json"))
    st.json(payload) if payload else empty_state_panel("JSON bulunamadı", "Hiperparametre raporu mevcut değil.")
    with st.expander("GridSearchCV sonuçları", expanded=False):
        metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/hyperparameter_search_results.csv")))
    section_heading("Özellik önemi")
    metric_table(load_csv_safe(str(REGRESSION_DIR / "outputs/feature_importance.csv")))


def _residuals() -> None:
    columns = st.columns(2)
    for column, filename, title in [(columns[0], "residual_plot.png", "Artık analizi"),
                                     (columns[1], "prediction_vs_actual.png", "Tahmin ve gerçek")]:
        with column:
            section_heading(title)
            image = load_image_path_safe(str(REGRESSION_DIR / "outputs" / filename))
            if image: st.image(image, use_column_width=True)
            else: empty_state_panel("Görsel bulunamadı", filename)


def render() -> None:
    hero_panel("California Housing Regresyonu", "Yerel veri, leakage-safe pipeline, gerçek test metrikleri ve canlı tahmin deneyimi.", "MACHINE LEARNING")
    tabs = st.tabs(["Proje Özeti", "Tekli Tahmin", "Toplu Tahmin", "Model Performansı", "Artık Analizi", "Veri Kaynağı"])
    with tabs[0]:
        project = project_by_id("regression")
        metrics = load_csv_safe(str(REGRESSION_DIR / "outputs/test_metrics.csv"))
        columns = st.columns(3)
        for column, name in zip(columns, ["RMSE", "MAE", "R2"]):
            value = float(metrics.iloc[0][name]) if not metrics.empty and name in metrics else None
            column.metric(name, "—" if value is None else f"{value:.4f}")
        information_panel("Amaç", project["description"])
        information_panel("Veri ve model", f"{project['dataset']} ({project['dataset_size']}) · {project['final_model']}")
        information_panel("İş akışı", "Yerel veri → EDA → hedef-bağımsız oranlar → preprocessing → SelectKBest → 5-fold CV → tuning → test")
        information_panel("Sınırlamalar", "; ".join(project["limitations"]))
        with st.expander("Teknik detaylar", expanded=False):
            artifact_checklist(project)
    with tabs[1]: _single_prediction()
    with tabs[2]: _batch_prediction()
    with tabs[3]: _performance()
    with tabs[4]: _residuals()
    with tabs[5]:
        source = load_text_safe(str(REGRESSION_DIR / "DATA_SOURCE.md"))
        st.markdown(source) if source else empty_state_panel("Kaynak belgesi yok", "DATA_SOURCE.md bulunamadı.")

"""Streamlit interface for the offline California Housing regressor."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

def render_safe_table(frame,**_kwargs):
    """Render escaped semantic HTML without Streamlit's Arrow layer."""
    st.markdown(frame.to_html(index=False,escape=True),unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "regression_model.pkl"
OUTPUTS = BASE_DIR / "outputs"
RAW_COLUMNS = ["MedInc", "HouseAge", "AveRooms", "AveBedrms", "Population", "AveOccup", "Latitude", "Longitude"]

st.set_page_config(page_title="California Housing Regression", page_icon="🏠", layout="wide")


@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model bulunamadı; önce train_model.py çalıştırın.")
    return joblib.load(MODEL_PATH)


def prepare(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["RoomsPerBedroom"] = result["AveRooms"] / result["AveBedrms"].replace(0, np.nan)
    result["BedroomsPerOccupant"] = result["AveBedrms"] / result["AveOccup"].replace(0, np.nan)
    return result


def safe_csv(name: str) -> pd.DataFrame:
    path = OUTPUTS / name
    try:
        return pd.read_csv(path) if path.exists() else pd.DataFrame()
    except (OSError, pd.errors.ParserError):
        return pd.DataFrame()


st.title("🏠 California Housing Regression")
page = st.sidebar.radio("Sayfa", ["Tek Tahmin", "Toplu CSV", "Model Performansı"])

try:
    model = load_model()
except Exception as error:
    st.error(str(error)); st.stop()

if page == "Tek Tahmin":
    st.subheader("Bölge özelliklerini girin")
    defaults = [3.87, 28.6, 5.43, 1.10, 1425.0, 3.07, 35.63, -119.57]
    values = {}
    columns = st.columns(2)
    for index, (name, default) in enumerate(zip(RAW_COLUMNS, defaults)):
        values[name] = columns[index % 2].number_input(name, value=float(default), format="%.4f")
    if st.button("Tahmin Et"):
        prediction = float(model.predict(prepare(pd.DataFrame([values])))[0])
        st.metric("Tahmini Medyan Ev Değeri", f"${prediction * 100_000:,.0f}")
        st.caption("Eğitim hedefi 100.000 USD birimindedir; sonuç nedensel veya ekspertiz değeri değildir.")

elif page == "Toplu CSV":
    uploaded = st.file_uploader("CSV yükleyin", type="csv")
    if uploaded:
        frame = pd.read_csv(uploaded)
        missing = [column for column in RAW_COLUMNS if column not in frame]
        if missing:
            st.error("Eksik sütunlar: " + ", ".join(missing))
        else:
            result = frame.copy(); result["PredictedValue100kUSD"] = model.predict(prepare(frame[RAW_COLUMNS]))
            render_safe_table(result)
            st.download_button("Sonuçları indir", result.to_csv(index=False).encode(), "regression_predictions.csv", "text/csv")

else:
    st.subheader("Model performansı")
    metrics = safe_csv("test_metrics.csv")
    validation = safe_csv("validation_results.csv")
    importance = safe_csv("feature_importance.csv")
    if metrics.empty: st.info("Test metrikleri bulunamadı.")
    else: render_safe_table(metrics.round(4))
    if validation.empty: st.info("Validation sonuçları bulunamadı.")
    else: render_safe_table(validation.round(4))
    if importance.empty: st.info("Özellik önemleri bulunamadı.")
    else: render_safe_table(importance.round(4))
    col1, col2 = st.columns(2)
    for column, filename, title in [(col1, "residual_plot.png", "Residual"), (col2, "prediction_vs_actual.png", "Tahmin vs Gerçek")]:
        path = OUTPUTS / filename
        with column:
            st.markdown(f"#### {title}")
            if path.exists(): st.image(str(path), use_column_width=True)

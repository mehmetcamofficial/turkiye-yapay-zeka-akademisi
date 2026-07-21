"""Streamlit interface for the offline UCI sentiment classifier."""

from pathlib import Path
import re

import joblib
import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "nlp_pipeline.pkl"
OUTPUTS = BASE_DIR / "outputs"

st.set_page_config(page_title="Sentiment Classification", page_icon="💬", layout="wide")


@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model bulunamadı; önce train_model.py çalıştırın.")
    return joblib.load(MODEL_PATH)


def confidence(model, texts: pd.Series | list[str]) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(texts).max(axis=1)
    scores = np.abs(model.decision_function(texts))
    return 1 / (1 + np.exp(-scores))


def clean_text(text: str) -> str:
    """Mirror the deterministic cleaning used by train_model.py."""
    value = re.sub(r"<[^>]+>", " ", str(text))
    value = re.sub(r"https?://\S+|www\.\S+", " URL ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def safe_csv(filename: str) -> pd.DataFrame:
    path = OUTPUTS / filename
    try:
        return pd.read_csv(path) if path.exists() else pd.DataFrame()
    except (OSError, pd.errors.ParserError):
        return pd.DataFrame()


st.title("💬 English Sentiment Classification")
st.caption("UCI Sentiment Labelled Sentences · CC BY 4.0 · Amazon, IMDb, Yelp")
page = st.sidebar.radio("Sayfa", ["Tek Metin", "Toplu CSV", "Model Performansı"])
try:
    model = load_model()
except Exception as error:
    st.error(str(error)); st.stop()

if page == "Tek Metin":
    text = st.text_area("İngilizce değerlendirme", "This product works perfectly and I love it.")
    if st.button("Duyguyu Tahmin Et"):
        prepared = [clean_text(text)]
        prediction = int(model.predict(prepared)[0]); probability = float(confidence(model, prepared)[0])
        st.metric("Tahmin", "Positive" if prediction == 1 else "Negative")
        st.metric("Model güven skoru", f"{probability:.1%}")
        st.caption("Güven skoru kalibre edilmiş olasılık olmayabilir ve üretim garantisi değildir.")

elif page == "Toplu CSV":
    uploaded = st.file_uploader("`text` sütunu içeren CSV yükleyin", type="csv")
    if uploaded:
        frame = pd.read_csv(uploaded)
        if "text" not in frame: st.error("`text` sütunu bulunamadı.")
        else:
            prepared = frame["text"].fillna("").map(clean_text)
            result = frame.copy(); result["label"] = model.predict(prepared)
            result["sentiment"] = result["label"].map({0: "negative", 1: "positive"}); result["confidence"] = confidence(model, prepared)
            st.dataframe(result, use_container_width=True, hide_index=True)
            st.download_button("Sonuçları indir", result.to_csv(index=False).encode(), "sentiment_predictions.csv", "text/csv")

else:
    st.subheader("Model performansı")
    for filename, title in [("test_metrics.csv", "Test"), ("validation_results.csv", "Validation + CV"),
                            ("top_terms.csv", "En güçlü terimler"), ("error_analysis.csv", "Hata analizi")]:
        st.markdown(f"#### {title}"); frame = safe_csv(filename)
        if frame.empty: st.info(f"{filename} bulunamadı veya boş.")
        else: st.dataframe(frame.head(100).round(4), use_container_width=True, hide_index=True)
    image = OUTPUTS / "confusion_matrix.png"
    if image.exists(): st.image(str(image), use_column_width=True)

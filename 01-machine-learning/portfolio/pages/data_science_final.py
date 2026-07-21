"""Planned Data Science final-project page."""

import streamlit as st

from portfolio.config import DATA_SCIENCE_FINAL_DIR
from portfolio.data_science_registry import evaluate_final_project
from portfolio.loaders import load_text_safe
from portfolio.ui_components import hero_panel, information_panel, status_badge


def render() -> None:
    item = evaluate_final_project()
    hero_panel("Trendyol Search Relevance Intelligence", "Gerçek query-product relevance şemasında doğrulanmış V1 baseline ve planlanan V2 geliştirmeleri.", "DATA ANALYTICS")
    st.markdown(status_badge(item["status"]), unsafe_allow_html=True)
    tabs = st.tabs(["Proje Vizyonu", "Veri Kaynağı", "Şema Analizi", "Planlanan Analizler", "Modelleme Fırsatları", "Yol Haritası", "Teknik Detaylar"])
    with tabs[0]: information_panel("Vizyon", "Ürün kataloğu kalitesi, kategori/marka yapısı ve metin keşfini gerçek sütunlara göre birleştirmek.")
    with tabs[1]: st.markdown(load_text_safe(str(DATA_SCIENCE_FINAL_DIR/"DATA_SOURCE.md")))
    with tabs[2]: information_panel("Şema doğrulandı", "Query, title, category, brand, attributes, label ve sample_weight alanları belgeli; işlem/müşteri alanları varsayılmaz.")
    with tabs[3]:
        information_panel("Profil ve kalite", "Eksik/duplicate ürün, kategori/marka dağılımı, başlık ve açıklama istatistikleri.")
        information_panel("Koşullu analiz", "Fiyat alanı varsa fiyat; metin alanı varsa metin kalitesi ve TF-IDF analizi.")
    with tabs[4]: information_panel("Modelleme", "Term-group validation ile word Logistic Regression ve char LinearSVC karşılaştırıldı; seçilen V1 pipeline bağımsız ML projesinde doğrulandı.")
    with tabs[5]: information_panel("Yol haritası", "Resmî brief → veri/lisans → şema → EDA → koşullu modelleme → Streamlit → test ve teslim.")
    with tabs[6]:
        for name in ["PROJECT_PLAN.md", "EXPERIMENT_PLAN.md", "DATA_DICTIONARY.md", "MODEL_CARD_TEMPLATE.md", "RISK_AND_LIMITATIONS.md", "DEPLOYMENT_PLAN.md"]:
            with st.expander(name, expanded=False): st.markdown(load_text_safe(str(DATA_SCIENCE_FINAL_DIR/name)))

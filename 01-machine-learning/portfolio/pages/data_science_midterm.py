"""Trendyol data-quality and exploratory-analysis midterm workspace."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from portfolio.config import DATA_SCIENCE_MIDTERM_DIR, TRENDYOL_PROFILE_DIR
from portfolio.data_science_registry import evaluate_midterm
from portfolio.loaders import load_csv_safe, load_json_safe, load_text_safe
from portfolio.ui_components import hero_panel, information_panel, metric_table, status_badge

SCOPE = [
    "Veri envanteri", "Şema inceleme", "İlk/son kayıt kontrolü", "Eksik değerler", "Duplicate analizi",
    "Kategorik benzersizlik", "En sık kategoriler", "En sık markalar", "Başlık uzunluğu", "Attributes kalitesi",
    "Null-benzeri değerler", "Label dağılımı", "Pozitif/negatif örnekler", "Query-title örtüşmesi", "Temiz analiz örneği",
]


def _filter(frame: pd.DataFrame, **criteria: str) -> pd.DataFrame:
    result = frame.copy()
    for column, value in criteria.items():
        if column in result:
            result = result[result[column].astype(str) == value]
    return result


def render() -> None:
    item = evaluate_midterm()
    outputs = TRENDYOL_PROFILE_DIR / "outputs"
    hero_panel("Trendyol Veri Kalitesi ve Keşifsel Veri Analizi",
               "Gerçek ürün kataloğu ve arama alaka düzeyi tablolarının bounded, tekrar üretilebilir incelemesi.", "DATA ANALYTICS")
    st.markdown(status_badge(item["status"]), unsafe_allow_html=True)
    summary = [
        ("Veri seti", "Hazır" if item["inventory_ready"] else "Eksik"),
        ("Kaynak tablo", str(item["downloaded_file_count"])),
        ("Toplam boyut", f"{item['downloaded_size_bytes']/1024**3:.2f} GiB"),
        ("Profil örneği", "20.000 / tablo"),
        ("Üretilen çıktı", str(len(item["profile_outputs"]))),
        ("Tamamlanan kapsam", f"{item['completed_questions']}/15"),
        ("Notebook", "Hazır" if item["notebook_ready"] else "Eksik"),
        ("Son doğrulama", (item["last_verified"] or "—").replace("T", " ")),
    ]
    st.markdown('<div class="kpi-grid">' + "".join(f'<div class="kpi-card"><small>{a}</small><strong>{b}</strong></div>' for a,b in summary) + '</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Proje Özeti", "Veri Envanteri", "Veri Kalitesi", "Kategori ve Marka", "Metin Analizi",
                    "Alaka Etiketleri", "Temizlik Sonuçları", "Görselleştirmeler", "Notebook", "Çıktılar", "Teknik Detaylar"])
    with tabs[0]:
        information_panel("Amaç", "Ürün kataloğu, sorgu ve relevance tablolarında şema, kalite, kategori, marka ve metin özelliklerini incelemek.")
        metric_table(pd.DataFrame({"No": range(1, 16), "Uyarlanmış kapsam": SCOPE,
                                   "Durum": ["✓ Tamamlandı" if i <= item["completed_questions"] else "◐ Geliştiriliyor" for i in range(1,16)]}))
        information_panel("Sınırlamalar", "Profil dağılımları tablo başına ilk 20.000 satır örneğine aittir; tam veri performansı olarak yorumlanmamalıdır.")
        if st.button("Model geliştirme projesine geç", key="midterm_to_relevance"):
            st.session_state["requested_page"]="Trendyol Arama Alaka Zekâsı"; st.rerun()
    with tabs[1]:
        inventory = pd.DataFrame(item["inventory"])
        if not inventory.empty:
            inventory["size_mb"] = inventory["size_bytes"] / 1024**2
            metric_table(inventory[["relative_path", "extension", "size_mb", "row_count", "column_count", "readable"]])
    with tabs[2]:
        metric_table(load_csv_safe(str(outputs / "missing_values.csv")))
        metric_table(load_csv_safe(str(outputs / "duplicate_summary.csv")))
        metric_table(load_csv_safe(str(outputs / "cardinality_summary.csv")))
    with tabs[3]:
        categories = load_csv_safe(str(outputs / "categorical_summary.csv"))
        metric_table(_filter(categories, column="category"), "Kategori profili bulunamadı.")
        metric_table(_filter(categories, column="brand"), "Marka profili bulunamadı.")
    with tabs[4]:
        lengths = load_csv_safe(str(outputs / "text_length_summary.csv"))
        metric_table(lengths[lengths["column"].isin(["title", "query", "attributes"])] if "column" in lengths else lengths)
        information_panel("Yorum", "Başlık, sorgu ve attributes uzunlukları sampled profilden gelir; lexical-overlap analizi sonraki bounded çıktıdır.")
    with tabs[5]:
        labels = load_csv_safe(str(outputs / "categorical_summary.csv"))
        metric_table(_filter(labels, column="label"), "Label dağılımı bulunamadı.")
        information_panel("Kapsam", "Pozitif/negatif relevance örnekleri ve hata analizi final proje deney planına aktarılmıştır.")
    with tabs[6]:
        metric_table(load_csv_safe(str(outputs / "column_profile.csv")))
        information_panel("Temizlik", "Kaynak tablolar değiştirilmez. Null normalizasyonu ve metin temizleme kuralları analiz örneğine uygulanacak; ham veri korunacaktır.")
    with tabs[7]:
        information_panel("Görselleştirme durumu", "Persist edilmiş sayısal, kategorik ve metin özetleri hazır. Büyük tablolar sayfa açılışında yeniden çizilmez.")
    with tabs[8]:
        notebook = item["notebook_path"]
        information_panel("Notebook", f"35 hücreli notebook {'hazır' if notebook.is_file() else 'eksik'} · Colab {'yapılandırıldı' if item['colab_configured'] else 'henüz yayınlanmadı'}.")
        if notebook.is_file():
            st.download_button("Notebook'u indir", notebook.read_bytes(), notebook.name, "application/x-ipynb+json")
    with tabs[9]:
        files = [{"Çıktı": name, "Durum": "Hazır"} for name in item["profile_outputs"]]
        metric_table(pd.DataFrame(files))
    with tabs[10]:
        with st.expander("Özgün Ödev Şemasından Uyarlama Notu", expanded=False):
            st.markdown(load_text_safe(str(DATA_SCIENCE_MIDTERM_DIR / "SCHEMA_COMPATIBILITY.md")))
            st.info("Özgün ödeme, müşteri, sipariş, fiyat ve teslimat analizlerinin yapıldığı iddia edilmez. İnceleme gerçek Trendyol ürün ve relevance şemasına uyarlanmıştır.")
        with st.expander("Profil kapsamı ve veri kaynağı", expanded=False):
            st.markdown(load_text_safe(str(outputs / "profile_summary.md")))
            st.markdown(load_text_safe(str(DATA_SCIENCE_MIDTERM_DIR / "DATA_SOURCE.md")))

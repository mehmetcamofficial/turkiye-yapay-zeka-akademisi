"""Live Trendyol query-product relevance intelligence page."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.loaders import load_csv_safe,load_json_safe,load_text_safe
from portfolio.project_registry import project_by_id
from portfolio.trendyol_relevance_service import predict_batch,predict_single,rank_sample
from portfolio.ui_components import (empty_state_panel,hero_panel,information_panel,metric_table,
                                     prediction_result_card,render_safe_table,section_heading,status_badge)

def _single():
    with st.form("trendyol_relevance_single"):
        query=st.text_input("Arama sorgusu","kablosuz kulaklık")
        title=st.text_input("Ürün başlığı","Bluetooth kablosuz kulaklık")
        left,right=st.columns(2); category=left.text_input("Kategori"); brand=right.text_input("Marka")
        gender=left.text_input("Ürün gender alanı"); age_group=right.text_input("Ürün age_group alanı")
        attributes=st.text_area("Ürün özellikleri"); submitted=st.form_submit_button("Alaka Tahmini Oluştur")
    if submitted:
        try:
            result=predict_single(query=query,title=title,category=category,brand=brand,gender=gender,age_group=age_group,attributes=attributes)
            prediction_result_card("Tahmin",result["relevance_status"],f"Skor: {result['score']:.4f} · Tür: {result['score_type']} · Model: {result['model_version']}")
            metric_table(pd.DataFrame([{"Eşleşme sinyali":k,"Değer":v} for k,v in result["key_matching_signals"].items()]))
        except ValueError as exc: st.warning(str(exc))
        except Exception: st.error("Tahmin oluşturulamadı. Model artifact ve girdileri kontrol edin.")

def _batch():
    upload=st.file_uploader("Query ve title sütunlarını içeren CSV",type="csv",key="trendyol_relevance_batch")
    information_panel("Sınır", "Zorunlu: query, title. En fazla 10.000 kayıt; preview ilk 100 satırdır.")
    if upload is None: return
    try: frame=pd.read_csv(upload)
    except (UnicodeError,pd.errors.ParserError): st.error("CSV okunamadı."); return
    if st.button("Toplu tahmini çalıştır",key="trendyol_batch_run"):
        try:
            result=predict_batch(frame); st.session_state["trendyol_batch_result"]=result
        except ValueError as exc: st.warning(str(exc))
        except Exception: st.error("Toplu tahmin tamamlanamadı.")
    result=st.session_state.get("trendyol_batch_result")
    if isinstance(result,pd.DataFrame):
        render_safe_table(result,max_rows=100)
        st.download_button("Sonuçları indir",result.to_csv(index=False).encode("utf-8"),"trendyol_relevance_predictions.csv","text/csv")

def _playground():
    information_panel("Bounded katalog demosu", "Bu demo yalnızca sınırlı yerel aday örneğini sıralar; Trendyol kataloğunun tamamını sıralamaz.")
    query=st.text_input("Katalog sorgusu","kadın elbise",key="catalogue_query")
    catalogue=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/catalogue_sample.csv"))
    categories=[""]+sorted(catalogue["category"].dropna().astype(str).unique().tolist()) if "category" in catalogue else [""]
    category=st.selectbox("Kategori filtresi",categories,format_func=lambda x:x or "Tümü")
    if st.button("Sınırlı örnekte ara",key="rank_catalogue"):
        try:
            result=rank_sample(query,category,10)
            columns=[c for c in ["rank","title","category","brand","score","score_type"] if c in result]
            render_safe_table(result[columns],max_rows=10)
        except ValueError as exc: st.warning(str(exc))
        except Exception: st.error("Katalog örneği sıralanamadı.")

def render():
    project=project_by_id("trendyol_relevance"); metadata=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"models/model_metadata.json")); metrics=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/metrics.json"))
    hero_panel("Trendyol Arama Alaka Zekâsı", "Query-product ilişkisini term-group validation ve sparse lexical özelliklerle sınıflandıran ilk çalışan baseline.", "MACHINE LEARNING")
    st.markdown(status_badge(project["status"]),unsafe_allow_html=True)
    cards=[("Veri modu",metadata.get("data_mode","—")),("Satır",metadata.get("training_rows",0)+metadata.get("validation_rows",0)),("Validation","term_id group"),("Model",metadata.get("model_type","—")),("F1",f"{metrics.get('f1',0):.4f}"),("Artifact","Mevcut" if project["model_artifact_available"] else "Eksik"),("Canlı inference","Açık" if project["app_available"] else "Kapalı")]
    st.markdown('<div class="kpi-grid">'+''.join(f'<div class="kpi-card"><small>{a}</small><strong>{b}</strong></div>' for a,b in cards)+'</div>',unsafe_allow_html=True)
    tabs=st.tabs(["Proje Özeti","Canlı Alaka Tahmini","Toplu Tahmin","AI Playground","Model Performansı","Hata Analizi","Özellikler","Veri ve Split","Model Kartı","Teknik Detaylar"])
    with tabs[0]:
        information_panel("Problem",project["description"]); information_panel("Seçim",load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/model_selection.md")))
        information_panel("Sınırlamalar","; ".join(project["limitations"]))
        if st.button("Veri profili ve EDA sonuçlarını görüntüle",key="to_trendyol_eda"): st.session_state["requested_page"]="Trendyol Ara Proje"; st.rerun()
    with tabs[1]: _single()
    with tabs[2]: _batch()
    with tabs[3]: _playground()
    with tabs[4]:
        metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/model_comparison.csv"))); metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/classification_report.csv")))
        image=TRENDYOL_RELEVANCE_DIR/"outputs/model_comparison.png"; st.image(str(image)) if image.is_file() else None
    with tabs[5]:
        metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/category_performance.csv")))
        metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/lexical_overlap_performance.csv")))
        with st.expander("Error analysis özeti"): st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/error_analysis.md")))
    with tabs[6]: st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/feature_dictionary.md")))
    with tabs[7]:
        split=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/split_report.json")); metric_table(pd.DataFrame([{k:v for k,v in split.items() if k!="comparison"}]))
    with tabs[8]: st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"README.md")))
    with tabs[9]:
        with st.expander("Relative artifact yolları",expanded=False): st.code("01-machine-learning/trendyol-search-relevance/models/\n01-machine-learning/trendyol-search-relevance/outputs/\n01-machine-learning/trendyol-search-relevance/reports/")

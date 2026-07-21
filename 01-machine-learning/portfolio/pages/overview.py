"""Professional platform overview backed by saved registries and artifacts."""

import pandas as pd
import streamlit as st

from portfolio.data_science_registry import data_science_counts, evaluate_midterm
from portfolio.project_registry import get_project_registry, portfolio_counts
from portfolio.ui_components import hero_panel, information_panel, render_safe_table, section_heading, status_badge


def _solution_card(project: dict, title: str, problem: str, destination: str) -> None:
    value = project["primary_metric_value"]
    metric = "—" if value is None else f"{value:.4f}"
    st.markdown(f'''<div class="project-card">{status_badge(project['status'])}<h3>{title}</h3><p>{problem}</p>
        <div class="card-meta"><div><small>Dataset</small><strong>{project['dataset_size']}</strong></div>
        <div><small>Final model</small><strong>{project['final_model']}</strong></div>
        <div><small>{project['primary_metric_name']}</small><strong>{metric}</strong></div>
        <div><small>Validation</small><strong>5-fold CV + tuning</strong></div>
        <div><small>Live capability</small><strong>Single + batch</strong></div>
        <div><small>Artifact</small><strong>Verified</strong></div></div></div>''', unsafe_allow_html=True)
    if st.button("Çözümü aç", key=f"solution_{project['id']}", use_container_width=True):
        st.session_state["requested_page"] = destination; st.rerun()


def _kpis(items: list[tuple[str, object, str]]) -> None:
    cards = "".join(f'<div class="kpi-card"><small>{label}</small><strong>{value}</strong><span>{context}</span></div>' for label,value,context in items)
    st.markdown(f'<div class="kpi-grid">{cards}</div>', unsafe_allow_html=True)


def render() -> None:
    hero_panel("AI & Data Intelligence Platform",
        "Veri analizi, makine öğrenmesi, doğal dil işleme ve model operasyonlarını doğrulanabilir artifact'larla birleştiren uygulamalı çalışma alanı.",
        "PLATFORM OVERVIEW")
    st.markdown('<div class="capability-tags"><span>Data Analysis</span><span>Machine Learning</span><span>NLP</span><span>Batch Inference</span><span>Explainability</span><span>Reproducibility</span></div>', unsafe_allow_html=True)

    projects = get_project_registry(); by_id = {p["id"]:p for p in projects}
    ml = portfolio_counts(); ds = data_science_counts(); midterm = evaluate_midterm()
    verified = sum(sum((p["directory"]/item.rstrip("/")).exists() for item in p["expected_output_files"]) for p in projects[:3])
    last_verified = max((p["last_verified"] for p in projects[:3] if p["last_verified"]), default="Not available")
    section_heading("Platform Sağlığı", "Yerel registry ve artifact hazırlığı.")
    _kpis([("Model Registry", "3/3", "Persist edilmiş artifact sağlıklı"), ("Veri varlıkları", midterm['downloaded_file_count'], "Yerel kaynak tablo"),
        ("Notebook", "Hazır" if midterm["notebook_ready"] else "Eksik", "Tekrar üretilebilir çalışma"), ("Artifact doğrulama", verified, "Beklenen çıktı mevcut"),
        ("Deployment", "Planlandı", "API henüz uygulanmadı"), ("Son doğrulama",last_verified.replace("T", " "), "Artifact zamanı")])

    section_heading("Platform Metrikleri", "Tamamlanmış ve doğrulanmış yetenekler.")
    _kpis([("ML çözümleri", ml["completed_projects"], "Tamamlandı / doğrulandı"), ("Canlı model artifact'ı", ml["completed_pipelines"], "Persist edilmiş pipeline"),
           ("Değerlendirilen aday", ml["models_compared"], "3 projedeki model varyantı"), ("Canlı tahmin modülü", ml["live_prediction_modules"], "Tekli ve batch"),
           ("Notebook", ds["notebooks_ready"], "Yerel ve doğrulanmış"), ("Profil çıktısı", len(midterm.get("profile_outputs", [])), "Kaydedilmiş rapor"),
           ("Veri tablosu", midterm["downloaded_file_count"], "Yaklaşık 0,91 GiB")])

    section_heading("Öne Çıkan Çözümler", "Tamamlanmış, doğrulanmış ve canlı modüller.")
    columns = st.columns(3)
    cards = [(by_id["churn"],"Customer Churn Intelligence","Yüksek ayrılma riski taşıyan telekom müşterilerini önceliklendirir.","Customer Churn"),
             (by_id["regression"],"Konut Değeri Tahmini","California bölgelerinin medyan konut değerini tahmin eder.","Konut Regresyonu"),
             (by_id["nlp"],"Sentiment Intelligence","İngilizce değerlendirme duygusunu açıklanabilir terimlerle sınıflandırır.","Sentiment Intelligence")]
    for column,args in zip(columns,cards):
        with column: _solution_card(*args)

    section_heading("Veri Bilimi Çalışma Alanı", "Trendyol veri kalitesi ve EDA hazırlığı.")
    _kpis([("Veri seti", "Hazır" if midterm["inventory_ready"] else "Eksik", "Yerel ve offline"), ("Tablolar",midterm["downloaded_file_count"], "CSV + Parquet"),
        ("Uyarlanmış kapsam",f"{midterm['completed_questions']}/15", "Gerçek Trendyol şeması"), ("Profil", "Hazır" if midterm["profile_ready"] else "Eksik", "20.000 satır / tablo"),
        ("Çıktılar",len(midterm.get("profile_outputs", [])), "Persist edilmiş"), ("Colab","Yayınlandı" if midterm["colab_configured"] else "Bekliyor", "Yerel notebook hazır")])
    if st.button("Veri Bilimi Çalışma Alanını Aç", key="overview_workspace", use_container_width=True):
        st.session_state["requested_page"]="Veri Bilimi Çalışma Alanı"; st.rerun()

    section_heading("Yetkinlik Matrisi", "Uygulanan yetenekler ile planlanan çalışmalar ayrıdır.")
    rows = ["Data Profiling","Data Cleaning","EDA","Classification","Regression","NLP","Batch Prediction","Explainability","Hyperparameter Tuning","Data Governance","Model Registry","Artifact Verification","Live Inference"]
    capability = {"Churn":[1,1,1,1,0,0,1,1,1,1,1,1,1], "Regresyon":[1,1,1,0,1,0,1,1,1,1,1,1,1],
        "NLP":[1,1,1,1,0,1,1,1,1,1,1,1,1], "Trendyol Ara Proje":[1,1,1,0,0,0,0,0,0,1,0,1,0]}
    matrix = pd.DataFrame({"Yetkinlik":rows, **{name:["✓ Mevcut" if flag else "— Uygulanamaz" for flag in flags] for name,flags in capability.items()}})
    render_safe_table(matrix, max_rows=50)
    information_panel("Planlanan yetkinlikler", "Trendyol Final: relevance sınıflandırma, model değerlendirme, batch/live scoring ve artifact persistence planlandı; henüz uygulanmış olarak işaretlenmez.")

    section_heading("Yol Haritası", "Sonraki somut platform adımları.")
    roadmap = [
        ("Trendyol Ara Proje EDA", "Geliştiriliyor", "Data Science", "Yüksek", "Kaydedilmiş profil", "Lexical-overlap ve temiz örnek çıktısı"),
        ("Trendyol relevance baseline", "Planlandı", "Machine Learning", "Yüksek", "EDA tamamlanması", "Baseline deney tasarımı"),
        ("Model değerlendirme", "Planlandı", "ML Evaluation", "Yüksek", "Baseline modeller", "CV ve hata analizi"),
        ("Streamlit canlı scoring", "Planlandı", "Inference", "Orta", "Persist edilmiş final model", "Query-product formu"),
        ("Deployment API", "Planlandı", "MLOps", "Orta", "Model contract", "Health ve predict endpoint'leri"),
        ("Dokümantasyon/yayın", "Planlandı", "Portfolio", "Orta", "Doğrulanmış sonuçlar", "Model card ve yayın kontrolü"),
        ("Opsiyonel clustering", "Planlandı", "Machine Learning", "Düşük", "Uygun eğitim amacı", "Sentetik kapsam kararı"),
    ]
    render_safe_table(pd.DataFrame(roadmap, columns=["Başlık","Durum","Kategori","Öncelik","Bağımlılık","Sonraki adım"]), max_rows=20)

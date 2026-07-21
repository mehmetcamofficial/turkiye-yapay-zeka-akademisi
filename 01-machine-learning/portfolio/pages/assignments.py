"""Academy assignment status from real ML and Data Science artifacts."""

import pandas as pd
import streamlit as st

from portfolio.data_science_registry import evaluate_final_project, evaluate_midterm
from portfolio.project_registry import project_by_id
from portfolio.ui_components import hero_panel, render_safe_table, section_heading, status_badge


def _assignment_card(item: dict, destination: str | None) -> None:
    st.markdown(f'''<div class="project-card">{status_badge(item['status'])}<h3>{item['name']}</h3>
        <p>{item['description']}</p><div class="card-meta">
        <div><small>Kategori</small><strong>{item['category']}</strong></div>
        <div><small>Artifact</small><strong>{item['artifact']}</strong></div>
        <div><small>Veri kaynağı</small><strong>{item['data_source']}</strong></div>
        <div><small>Teslim hazırlığı</small><strong>{item['delivery']}</strong></div>
        </div></div>''', unsafe_allow_html=True)
    if st.button("Detayları aç", key=f"assignment_{item['id']}", disabled=destination is None, use_container_width=True):
        st.session_state["requested_page"] = destination
        st.rerun()


def render() -> None:
    hero_panel("Akademi Ödevleri", "Makine öğrenmesi ve veri bilimi teslimlerinin artifact-driven durum ekranı.", "TÜRKİYE YAPAY ZEKA AKADEMİSİ")
    churn = project_by_id("churn"); midterm = evaluate_midterm(); final = evaluate_final_project()
    items = [
        {"id":"ml_final", "name":"Makine Öğrenmesi Final Ödevi", "category":"Makine Öğrenmesi",
         "status":churn["status"], "description":"Churn sınıflandırma pipeline'ı, model karşılaştırma ve Streamlit tahmini.",
         "artifact":"Mevcut" if churn["model_artifact_available"] else "Eksik", "data_source":"README belgeli", "delivery":"Hazır" if churn["status"]=="Tamamlandı" else "Eksik"},
        {"id":midterm["id"], "name":midterm["name"], "category":"Veri Bilimi",
         "status":midterm["status"], "description":"15 soruluk veri inceleme ve temizleme notebook'u.",
         "artifact":f"{len(midterm['existing_outputs'])}/{len(midterm['expected_outputs'])} output", "data_source":"Belgeli" if midterm["data_source_documented"] else "Eksik",
         "delivery":"Colab bekleniyor" if not midterm["colab_configured"] else "Yayınlandı"},
        {"id":final["id"], "name":"Veri Bilimi Final Projesi", "category":"Veri Bilimi",
         "status":"Planlandı", "description":"Trendyol Search & Product Intelligence; deney ve model artifact'ları henüz üretilmedi.",
         "artifact":"Plan dosyası mevcut", "data_source":"Belgeli", "delivery":"Planlandı"},
    ]
    columns = st.columns(3)
    destinations = ["Customer Churn", "Trendyol Ara Proje", "Trendyol Final Projesi"]
    for column, item, destination in zip(columns, items, destinations):
        with column: _assignment_card(item, destination)
    section_heading("Erişilebilir durum tablosu")
    render_safe_table(pd.DataFrame(items).drop(columns=["description"]), max_rows=20)

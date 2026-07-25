from __future__ import annotations

import streamlit as st

LANGUAGES = {"tr": "Türkçe", "en": "English"}

DEFAULT_LANG = "tr"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "nav_overview": {"tr": "GENEL BAKIŞ", "en": "OVERVIEW"},
    "nav_executive_overview": {"tr": "Yönetici Özeti", "en": "Executive Overview"},
    "nav_portfolio_highlights": {"tr": "Portföy Öne Çıkanlar", "en": "Portfolio Highlights"},
    "nav_search": {"tr": "ARAMA ZEKÂSI", "en": "SEARCH INTELLIGENCE"},
    "nav_search_demo": {"tr": "Arama Demosu", "en": "Search Demo"},
    "nav_cross_encoder": {"tr": "Cross-Encoder Reranking", "en": "Cross-Encoder Reranking"},
    "nav_eval_lab": {"tr": "Değerlendirme Laboratuvarı", "en": "Evaluation Lab"},
    "nav_architecture": {"tr": "Mimari", "en": "Architecture"},
    "nav_ml": {"tr": "MAKİNE ÖĞRENMESİ", "en": "MACHINE LEARNING"},
    "nav_churn": {"tr": "Müşteri Kaybı", "en": "Customer Churn"},
    "nav_housing": {"tr": "Konut Regresyonu", "en": "Housing Regression"},
    "nav_sentiment": {"tr": "Duygu Analizi", "en": "Sentiment Intelligence"},
    "nav_data_quality": {"tr": "VERİ VE KALİTE", "en": "DATA & QUALITY"},
    "nav_data_workspace": {"tr": "Trendyol Veri Çalışma Alanı", "en": "Trendyol Data Workspace"},
    "nav_inventory": {"tr": "Veri Envanteri", "en": "Dataset Inventory"},
    "nav_quality": {"tr": "Veri Kalitesi", "en": "Data Quality"},
    "nav_schema": {"tr": "Şema ve Profilleme", "en": "Schema & Profiling"},
    "nav_model_ops": {"tr": "MODEL OPERASYONLARI", "en": "MODEL OPERATIONS"},
    "nav_registry": {"tr": "Model Registry", "en": "Model Registry"},
    "nav_artifact_health": {"tr": "Artifact Sağlığı", "en": "Artifact Health"},
    "nav_deployment": {"tr": "Dağıtım Hazırlığı", "en": "Deployment Readiness"},
    "nav_portfolio": {"tr": "PORTFÖY", "en": "PORTFOLIO"},
    "nav_projects": {"tr": "Projeler", "en": "Projects"},
    "nav_docs": {"tr": "Dokümantasyon", "en": "Documentation"},
    "nav_about": {"tr": "Mehmet Hakkında", "en": "About Mehmet"},
    "nav_academic": {"tr": "AKADEMİK ARŞİV", "en": "ACADEMIC ARCHIVE"},
    "nav_assignments": {"tr": "Ödevler", "en": "Assignments"},
    "nav_notebook_status": {"tr": "Notebook Durumu", "en": "Notebook Status"},
    "nav_roadmap": {"tr": "Yol Haritası", "en": "Roadmap"},
    "nav_search_relevance": {"tr": "Trendyol Alaka Sınıflandırması", "en": "Trendyol Relevance Classification"},
    "nav_search_ranking": {"tr": "Trendyol Ürün Sıralaması", "en": "Trendyol Product Ranking"},
    "nav_pipeline_diagnostics": {"tr": "Trendyol Pipeline Teşhisi", "en": "Trendyol Pipeline Diagnostics"},
    "nav_data_science_midterm": {"tr": "Veri Bilimi Ara Sınav", "en": "Data Science Midterm"},
    "nav_data_science_final": {"tr": "Veri Bilimi Final", "en": "Data Science Final"},
    "section_overview": {"tr": "GENEL BAKIŞ", "en": "OVERVIEW"},
    "section_ml": {"tr": "MAKİNE ÖĞRENMESİ", "en": "MACHINE LEARNING"},
    "section_search": {"tr": "ARAMA ZEKÂSI", "en": "SEARCH INTELLIGENCE"},
    "section_data_science": {"tr": "VERİ BİLİMİ", "en": "DATA SCIENCE"},
    "section_model_ops": {"tr": "MODEL OPERASYONLARI", "en": "MODEL OPERATIONS"},
    "section_portfolio": {"tr": "PORTFÖY", "en": "PORTFOLIO"},

    "sidebar_brand": {"tr": "AI & Veri Bilimi Portföyü", "en": "AI & Data Science Portfolio"},
    "sidebar_subtitle": {"tr": "Türkiye Yapay Zeka Akademisi", "en": "Applied Analytics & Machine Learning"},
    "sidebar_language": {"tr": "Dil", "en": "Language"},
    "sidebar_summary": {"tr": "PORTFÖY ÖZETİ", "en": "PORTFOLIO SUMMARY"},
    "sidebar_completed": {"tr": "Tamamlanan", "en": "Completed"},
    "sidebar_models": {"tr": "Modeller", "en": "Models"},
    "sidebar_pipelines": {"tr": "Pipeline", "en": "Pipelines"},
    "sidebar_live": {"tr": "Canlı modül", "en": "Live modules"},
    "sidebar_data_science": {"tr": "Veri bilimi", "en": "Data science"},
    "sidebar_assignments": {"tr": "tamamlandı", "en": "completed"},
    "sidebar_verified": {"tr": "Yerel doğrulama aktif", "en": "Local verification active"},

    "status_verified": {"tr": "Doğrulandı", "en": "Verified"},
    "status_available": {"tr": "Kullanılabilir", "en": "Available"},
    "status_experimental": {"tr": "Deneysel", "en": "Experimental"},
    "status_limited": {"tr": "Sınırlı", "en": "Limited"},
    "status_archived": {"tr": "Arşivlendi", "en": "Archived"},
    "status_roadmap": {"tr": "Yol Haritasında", "en": "Roadmap"},
    "status_unavailable": {"tr": "Kullanılamıyor", "en": "Unavailable"},
    "status_error": {"tr": "Hata", "en": "Error"},
    "status_present": {"tr": "Mevcut", "en": "Present"},
    "status_missing": {"tr": "Eksik", "en": "Missing"},

    "error_page_load": {"tr": "Bu modül yüklenemedi. Diğer portföy sayfalarını kullanabilirsiniz.", "en": "This module could not be loaded. Please use other portfolio pages."},
    "error_render": {"tr": "Bu sayfa geçici olarak görüntülenemiyor.", "en": "This page is temporarily unavailable."},
    "error_detail": {"tr": "Teknik ayrıntı", "en": "Technical details"},
    "error_venv": {"tr": "Uygulamayı proje sanal ortamıyla başlatın.", "en": "Start the app with the project virtual environment."},

    "table_showing": {"tr": "{total} kaydın ilk {count} satırı gösteriliyor.", "en": "Showing first {count} of {total} records."},
    "table_download": {"tr": "CSV olarak indir", "en": "Download CSV"},
    "table_empty": {"tr": "Veri bulunamadı.", "en": "No data available."},
    "table_file": {"tr": "Dosya", "en": "File"},
    "table_type": {"tr": "Tür", "en": "Type"},
    "table_size": {"tr": "Boyut (MB)", "en": "Size (MB)"},
    "table_rows": {"tr": "Satır", "en": "Rows"},
    "table_columns": {"tr": "Sütun", "en": "Columns"},
    "table_sha256": {"tr": "SHA-256", "en": "SHA-256"},
    "table_readable": {"tr": "Okunabilir", "en": "Readable"},
    "table_status": {"tr": "Durum", "en": "Status"},
    "table_artifact": {"tr": "Artifact", "en": "Artifact"},
    "table_project": {"tr": "Proje", "en": "Project"},
    "table_category": {"tr": "Kategori", "en": "Category"},

    "subtitle_search_demo": {"tr": "Hibrit arama ve cross-encoder reranking kalıcı kanıtlarla.", "en": "Hybrid retrieval and cross-encoder reranking with persisted evidence."},
    "subtitle_architecture": {"tr": "Arama Zekası pipeline'ı ve portföy platformu için sistem mimarisi.", "en": "System architecture for the Search Intelligence pipeline and portfolio platform."},
    "subtitle_eval_lab": {"tr": "V2.1–V5 Trendyol arama deneyleri için değerlendirme sonuçları.", "en": "Evaluation results for V2.1–V5 Trendyol search experiments."},
    "subtitle_assignments": {"tr": "Veri bilimi ödevleri, notebook durumu ve tamamlanan Trendyol Arama Zekası araştırması.", "en": "Data science assignments, notebook status, and completed Trendyol Search Intelligence research."},
    "subtitle_notebook_status": {"tr": "Veri bilimi notebook'larının ve çıktılarının durumu.", "en": "Status of data science notebooks and outputs."},
    "subtitle_artifact_health": {"tr": "Temel portföy ve isteğe bağlı bileşenlerde artifact kullanılabilirliği.", "en": "Artifact availability across core portfolio and optional components."},
    "subtitle_deployment": {"tr": "Portföy uygulaması ve ML servislerinin güncel dağıtım durumu.", "en": "Current deployment status of the portfolio application and ML services."},
    "subtitle_model_registry": {"tr": "Kanıt destekli durum ile tüm kayıtlı projeler, araştırma adayları ve artifact'ler.", "en": "All registered projects, research candidates, and artifacts with evidence-backed status."},
    "subtitle_data_science_overview": {"tr": "Trendyol e-ticaret veri seti envanteri, şema, kalite ve profilleme.", "en": "Trendyol e-commerce dataset inventory, schema, quality, and profiling."},
    "subtitle_overview": {"tr": "Arama, sıralama ve makine öğrenmesi sistemlerini doğrulanabilir deneylerden çalışan portföy ürünlerine dönüştürüyorum.", "en": "I turn search, ranking, and ML experiments into verifiable, interactive portfolio systems."},
    "subtitle_trendyol_relevance": {"tr": "V1–V5 araştırma pipeline'ı: seyrek sınıflandırma, anlamsal erişim, hibrit füzyon, cross-encoder yeniden sıralama.", "en": "V1–V5 research pipeline: sparse classification, semantic retrieval, hybrid fusion, cross-encoder reranking."},
    "subtitle_projects": {"tr": "Tüm portföy projeleri güncel durum, metrik ve kanıtlarla.", "en": "All portfolio projects with current status, metrics, and evidence."},

    "ml_section_churn": {"tr": "Müşteri Kaybı Tahmini", "en": "Customer Churn Prediction"},
    "ml_section_housing": {"tr": "Konut Regresyonu", "en": "Housing Regression"},
    "ml_section_nlp": {"tr": "NLP Duygu Analizi", "en": "NLP Sentiment Analysis"},

    "filter_status": {"tr": "Duruma göre filtrele", "en": "Filter by status"},
    "filter_all": {"tr": "Tümü", "en": "All"},
    "id_label": {"tr": "ID", "en": "ID"},
    "status_label": {"tr": "Durum", "en": "Status"},
    "decision_label": {"tr": "Karar", "en": "Decision"},
    "algorithm_label": {"tr": "Algoritma", "en": "Algorithm"},
    "metric_label": {"tr": "Metrik", "en": "Metric"},
    "limitations_label": {"tr": "Sınırlamalar", "en": "Limitations"},
    "artifact_label": {"tr": "Artifact", "en": "Artifact"},
    "model_label": {"tr": "Model", "en": "Model"},
    "category_label": {"tr": "Kategori", "en": "Category"},
    "verified_label": {"tr": "Doğrulandı", "en": "Verified"},
    "available_label": {"tr": "Kullanılabilir", "en": "Available"},
    "experimental_label": {"tr": "Deneysel", "en": "Experimental"},
    "local_only_label": {"tr": "Yerel", "en": "Local-only"},
    "cloud_excluded_label": {"tr": "Cloud dışı", "en": "Cloud-excluded"},
    "confirmed_champions": {"tr": "Onaylanmış şampiyonlar", "en": "Confirmed champions"},
    "completed_pipelines": {"tr": "Tamamlanan pipeline'lar", "en": "Completed pipelines"},
    "research_candidates": {"tr": "Araştırma adayları", "en": "Research candidates"},
    "all_registered": {"tr": "Tüm kayıtlı projeler", "en": "All registered projects"},
    "total": {"tr": "Toplam", "en": "Total"},
    "ready": {"tr": "Hazır", "en": "Ready"},
    "not_available": {"tr": "Mevcut Değil", "en": "Not Available"},
    "available_status": {"tr": "Kullanılabilir", "en": "Available"},
    "unavailable_status": {"tr": "Kullanılamıyor", "en": "Unavailable"},
    "verified_status": {"tr": "Doğrulandı", "en": "Verified"},
    "unverified_status": {"tr": "Doğrulanmadı", "en": "Unverified"},
    "published": {"tr": "Yayınlandı", "en": "Published"},
    "not_published": {"tr": "Yayınlanmadı", "en": "Not Published"},
    "compatible": {"tr": "Uyumlu", "en": "Compatible"},
    "issues_label": {"tr": "Sorunlar", "en": "Issues"},
    "cloud_excluded_artifact": {"tr": "Cloud dışı bırakıldı", "en": "Excluded from cloud"},
}

TECHNICAL_TERMS = {
    "NDCG@10", "MRR", "RRF", "TF-IDF", "BM25",
    "Cross-Encoder", "item_id", "term_id", "SHA-256",
    "Recall@50", "Recall@100", "Precision@10", "MAP@10",
    "ROC AUC", "PR AUC", "RMSE", "MAE", "R²", "F1",
    "p95", "pkl", "joblib", "CSV", "JSON",
}


def get_language() -> str:
    return st.session_state.get("portfolio_language", DEFAULT_LANG)


def t(key: str, **kwargs: str | int | float) -> str:
    lang = get_language()
    translations = TRANSLATIONS.get(key, {})
    text = translations.get(lang) or translations.get(DEFAULT_LANG) or key
    if kwargs:
        text = text.format(**kwargs)
    return text


def is_technical(term: str) -> bool:
    return term in TECHNICAL_TERMS or any(c.isupper() for c in term if c.isalpha()) is False

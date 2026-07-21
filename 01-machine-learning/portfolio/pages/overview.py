"""Executive, employer-oriented platform landing page."""
import streamlit as st
from portfolio.project_registry import get_project_registry,portfolio_counts
from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.loaders import load_csv_safe,load_json_safe
from portfolio.ui_components import (architecture_flow,comparison_cards,evidence_strip,information_panel,
    page_header,project_card,render_safe_table,section_heading)

LINKS=[("Portfolio","https://mehmetcamofficial.com.tr/"),("LinkedIn","https://www.linkedin.com/in/mehmet-cam09/"),("GitHub","https://github.com/mehmetcamofficial")]

def go(label,destination,key):
    if st.button(label,key=key,use_container_width=True): st.session_state["requested_page"]=destination; st.rerun()

def render():
    projects=get_project_registry(); by={p["id"]:p for p in projects}; counts=portfolio_counts(); production=[p for p in projects if p["status"] in {"Tamamlandı","Doğrulandı","Hazır"} and p["model_artifact_available"]]; live=[p for p in projects if p["app_available"]]
    page_header("AI & Data Intelligence Platform","Sınıflandırma, regresyon, NLP, arama alakası, model değerlendirme ve model operasyonları boyunca uçtan uca makine öğrenmesi sistemleri. Mehmet Cam tarafından üretim odaklı bir AI mühendisliği portfolyosu olarak tasarlanıp geliştirildi.","AI ENGINEERING PORTFOLIO",LINKS)
    cols=st.columns(3)
    with cols[0]: go("Trendyol canlı demosunu aç","Trendyol Arama Alaka Zekâsı","hero_trendyol")
    with cols[1]: go("Model Registry’yi görüntüle","Model Registry","hero_registry")
    with cols[2]: go("Teknik mimariyi incele","Repository Guide","hero_docs")
    section_heading("Platform Durumu","Çalışma zamanından ve yerel registry’den türetilen doğrulanabilir durum.")
    evidence_strip([("Streamlit","Operational","Yerel sağlık kontrolü"),("Kayıtlı projeler",str(len(projects)),"Registry girdisi"),("Persist edilmiş pipeline",str(counts["completed_pipelines"]),"Yerel artifact"),("Canlı demo",str(len(live)),"Inference modülü"),("Arrow renderer","0 çağrı","Semantic HTML tablo"),("Sorgu leakage","0","term_id group split")])
    section_heading("Öne Çıkan Proje","Trendyol Search & Product Intelligence: doğru ürünü doğru sorguyla eşleştirme ve sıralama araştırması.")
    comparison_cards([
      {"title":"V1 Production-style Classifier","status":"Doğrulandı","kind":"champion","algorithm":"Logistic Regression · word/character TF-IDF","metric":"F1 0.6260 · PR AUC 0.7165","note":"Stabil probability inference; şampiyon korunuyor."},
      {"title":"V2 Historical Challenger","status":"Deneysel","kind":"experimental","algorithm":"Random Forest","metric":"Holdout F1 0.6384 · PR AUC 0.6909","note":"Historical Experimental Challenger · Not Promoted."},
      {"title":"V2.1 Best Research Candidate","status":"Terfi edilmedi","kind":"experimental","algorithm":"HistGradientBoosting · artifact not persisted","metric":"Mean F1 0.7539 · 95% CI 0.7461–0.7618","note":"Offline Evaluation · Different historical split · Direct superiority not established."},
      {"title":"V2.1 Search Ranker","status":"Terfi edilmedi","kind":"experimental","algorithm":"XGBoost rank:ndcg topk","metric":"Delta −0.0075 · CI −0.0234–0.0084","note":"Bounded Candidate Sample; baseline mean NDCG@10 0.8710."}])
    v3=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/v3_results.json")); v3_metrics=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/retrieval_metrics_by_seed.csv")); best=v3.get("best_tfidf","Combined TF-IDF")
    rows=v3_metrics[v3_metrics.method.eq(best)] if not v3_metrics.empty and "method" in v3_metrics else v3_metrics; recall=float(rows["recall@50"].mean()) if not rows.empty else 0
    v31=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/v31_results.json")); v31_metrics=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/v31_metrics_by_seed.csv")); candidate=v31.get("best_hybrid","semantic_e5_small"); candidate_rows=v31_metrics[v31_metrics.method.eq(candidate)] if not v31_metrics.empty and "method" in v31_metrics else v31_metrics; candidate_recall=float(candidate_rows["recall@50"].mean()) if not candidate_rows.empty else 0
    comparison_cards([{"title":"V3.1 Semantic Retrieval","status":"Deneysel","kind":"experimental","algorithm":f"multilingual E5 Small + {candidate}","metric":f"Recall@50 {candidate_recall:.4f} · {v3.get('catalogue',{}).get('bounded_rows',0):,} indexed products","note":"Bounded Demo · Offline Evaluation · Catalogue-Wide Not Established · governance report controls selection."}])
    architecture_flow([("Query","current"),("Candidate Retrieval","experimental"),("V1 Relevance Scoring","current"),("Ranking","experimental"),("Results","experimental")])
    cols=st.columns(2)
    with cols[0]: go("Canlı alaka tahmini","Trendyol Arama Alaka Zekâsı","featured_demo")
    with cols[1]: go("Model yönetişimini incele","Model Registry","featured_governance")
    section_heading("Canlı Yetenekler","Kullanılabilir ürün davranışları; planlanan yetenekler burada sayılmaz.")
    evidence_strip([("Sınıflandırma","Tekli + batch","Churn, sentiment, relevance"),("Regresyon","Tekli + batch","Konut değeri"),("Arama","Bounded ranking","5.000 ürün örneği"),("Operasyon","Registry + health","Reload ve checksum"),("Değerlendirme","Classification + ranking","CI ve hata analizi")])
    section_heading("Proje Portfolyosu","Dört çalışan makine öğrenmesi problemi.")
    ids=["churn","regression","nlp","trendyol_relevance"]; destinations={"churn":"Customer Churn","regression":"Konut Regresyonu","nlp":"Sentiment Intelligence","trendyol_relevance":"Trendyol Arama Alaka Zekâsı"}
    for row in [ids[:2],ids[2:]]:
        columns=st.columns(2)
        for column,pid in zip(columns,row):
            with column:
                p=by[pid]; project_card(p,"Projeyi incele")
                go("Canlı proje sayfasını aç",destinations[pid],f"overview_{pid}")
    section_heading("Engineering Evidence","Yumuşak iddialar yerine repository içinde doğrulanabilen kanıtlar.")
    evidence_strip([("Validation","term-group safe","Deterministik split"),("Artifact","Fresh-process reload","Metadata + checksum"),("Inference","Single + batch","Bounded contracts"),("Statistics","Query bootstrap","95% confidence interval"),("Governance","Champion/challenger","Terfi kararı kayıtlı"),("Repository","Raw data ignored","Branch checkpoint disiplini")])
    section_heading("Teknoloji ve Yetkinlik Haritası","Implemented, experimental ve planned durumları birbirinden ayrılır.")
    groups={"Data Engineering":"Schema validation · profiling · deterministic sampling · quality checks · feature pipelines","Machine Learning":"Logistic Regression · LinearSVC · Random Forest · boosting · calibration · classification metrics","NLP & Search":"Word/character TF-IDF · lexical overlap · relevance · learning to rank (Experimental)","Model Operations":"Persisted pipelines · registry · checksum · reload · batch inference","Responsible Evaluation":"Leakage prevention · holdout · bootstrap CI · limitation reporting","Next":"Multilingual embeddings · hybrid retrieval · cross-encoder reranking (Planned)"}
    render_safe_table([{"Alan":k,"Kapsam":v,"Durum":"Planned" if k=="Next" else ("Experimental" if "Experimental" in v else "Implemented")} for k,v in groups.items()],max_rows=10)
    section_heading("Platform Mimarisi","Artifact-driven yol: veri kaynağından izlenen canlı inference’a.")
    architecture_flow([("Data Sources","current"),("Validation","current"),("Feature Engineering","current"),("Training","current"),("Evaluation","current"),("Artifact Registry","current"),("Live Inference","current"),("Monitoring","planned")])
    section_heading("Araştırma Yol Haritası","Kompleksite yalnız tekrarlanabilir kanıt ürettiğinde artırılır.")
    information_panel("V2.1 robust evaluation","1.000 tam sorgu grubu, beş seed, aynı holdout sistem karşılaştırmaları ve hard-negative yeniden doğrulama.")
    information_panel("V3.1 semantic retrieval","Pinned multilingual E5, normalized NumPy dense retrieval and measured hybrid fusion are experimental; cross-encoder reranking remains planned.")
    section_heading("Profesyonel Profil","AI engineering, machine learning, data science ve ürün odaklı teknik sistemler.")
    st.caption("Bağlantılar yeni sekmede güvenli biçimde açılır: Portfolio · LinkedIn · GitHub")

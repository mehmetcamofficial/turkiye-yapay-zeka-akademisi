"""Guided Trendyol Search & Product Intelligence case study."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.loaders import load_csv_safe,load_json_safe,load_text_safe
from portfolio.project_registry import project_by_id
from portfolio.trendyol_relevance_service import predict_batch,predict_single,rank_sample
from portfolio.ui_components import (architecture_flow,comparison_cards,decision_banner,evidence_strip,information_panel,
    metric_table,model_stage_timeline,page_header,prediction_result_card,render_safe_table,section_heading,status_badge)

PRESETS=["kablosuz kulaklık","beyaz kadın sneaker","çocuk yağmurluk","erkek siyah pantolon","güneş gözlüğü"]

def classification_demo():
    preset=st.selectbox("Örnek sorgu",PRESETS,key="relevance_preset")
    with st.form("trendyol_relevance_single"):
        query=st.text_input("Arama sorgusu",preset); title=st.text_input("Ürün başlığı",preset.title())
        left,right=st.columns(2); category=left.text_input("Kategori"); brand=right.text_input("Marka"); gender=left.text_input("Gender"); age_group=right.text_input("Yaş grubu"); attributes=st.text_area("Ürün özellikleri"); submitted=st.form_submit_button("Alaka tahmini oluştur")
    if submitted:
        try:
            result=predict_single(query=query,title=title,category=category,brand=brand,gender=gender,age_group=age_group,attributes=attributes)
            prediction_result_card("V1 sonucu",result["relevance_status"],f"Probability: {result['score']:.4f} · Threshold: 0.50 · Version: {result['model_version']}")
            signals=pd.DataFrame([{"Model girdisi sinyali":k,"Değer":v,"Yorum":"Bu sinyal model girdisine katkı sağlar; nedensel açıklama değildir."} for k,v in result["key_matching_signals"].items()]); render_safe_table(signals,max_rows=20)
            st.caption("Lexical sinyaller semantik eşanlamlılığı bütünüyle temsil etmez; sonuç production kalite garantisi değildir.")
        except ValueError as exc: st.warning(str(exc))
        except Exception: st.error("Tahmin oluşturulamadı. Artifact ve girdileri kontrol edin.")

def batch_demo():
    upload=st.file_uploader("Query ve title sütunlarını içeren CSV",type="csv",key="trendyol_batch")
    st.caption("En fazla 10.000 kayıt; önizleme 100 satırla sınırlıdır.")
    if upload is None:return
    try: frame=pd.read_csv(upload)
    except (UnicodeError,pd.errors.ParserError): st.error("CSV okunamadı."); return
    if st.button("Toplu tahmini çalıştır",key="batch_run"):
        try: st.session_state["trendyol_batch_result"]=predict_batch(frame)
        except ValueError as exc: st.warning(str(exc))
        except Exception: st.error("Toplu tahmin tamamlanamadı.")
    result=st.session_state.get("trendyol_batch_result")
    if isinstance(result,pd.DataFrame): render_safe_table(result,max_rows=100,download_name="trendyol_predictions.csv")

def ranking_demo():
    mode=st.radio("Sıralama sistemi",["V1 classifier score","Experimental V2 holdout ranker"],horizontal=True)
    if mode.startswith("V1"):
        preset=st.selectbox("Örnek sorgu",PRESETS,key="rank_preset"); query=st.text_input("Sorgu",preset,key="rank_query"); limit=st.slider("Aday limiti",5,30,10)
        if st.button("Bounded kataloğu sırala",key="rank_run"):
            try:
                result=rank_sample(query,"",limit); result=result.rename(columns={"score":"V1 probability"}); render_safe_table(result[[c for c in ["rank","title","category","brand","V1 probability","score_type"] if c in result]],max_rows=30)
            except Exception: st.error("Bounded katalog sıralanamadı.")
        st.caption("V1 modu 5.000 ürünlük yerel örnek üzerinde çalışır; retrieval sistemi değildir.")
    else:
        frame=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v2/ranking_playground.csv"))
        decision_banner("Deneysel holdout görünümü","V2 ranker keyfi katalog girdisini destekleyen deploy edilmiş bir pipeline değildir; yalnız daha önce ayrılmış holdout adayları gösterilir.")
        if frame.empty: st.warning("V2 playground çıktısı yok."); return
        term=st.selectbox("Holdout query grubu",frame.term_id.drop_duplicates().tolist()); view=frame[frame.term_id.eq(term)].sort_values("rank_after"); view["rank_change"]=view.rank_before-view.rank_after
        render_safe_table(view[["query","title","label","first_stage_score","rank_before","final_ranking_score","rank_after","rank_change"]],max_rows=100)

def render():
    metadata=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"models/model_metadata.json")); metrics=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/metrics.json"))
    page_header("Trendyol Search & Product Intelligence","Bir kullanıcı sorgusuyla ürün arasındaki alaka düzeyini tahmin eden ve aday ürün sıralama challengers’ını sorumlu biçimde değerlendiren canlı vaka çalışması.","SEARCH RELEVANCE · CLASSIFICATION · RANKING")
    evidence_strip([("Current champion","V1 Logistic Regression","Doğrulandı"),("V1 F1",f"{metrics.get('f1',0):.4f}","term-group validation"),("V1 PR AUC",f"{metrics.get('pr_auc',0):.4f}","100k sample"),("V2 ranker NDCG@10","0.8044","Deneysel"),("First-stage NDCG@10","0.8477","Leakage-safe"),("term_id overlap","0","Group split")])
    decision_banner("Champion korundu","Daha karmaşık modeller, istatistiksel kanıt sağlamadığı için otomatik olarak üretim modelinin yerini almamıştır.")
    comparison_cards([{"title":"V1 Verified Champion","status":"Doğrulandı","kind":"champion","algorithm":"TF-IDF + similarity + Logistic Regression","metric":"F1 0.6260 · PR AUC 0.7165","note":"Stable live probability inference."},{"title":"V2 Historical Experimental Challenger","status":"Deneysel","kind":"experimental","algorithm":"Random Forest","metric":"Holdout F1 0.6384","note":"Not Promoted."},{"title":"V2.1 Best Research Candidate","status":"Terfi edilmedi","kind":"experimental","algorithm":"HistGradientBoosting · not persisted","metric":"Mean F1 0.7539 · CI 0.7461–0.7618","note":"Offline Evaluation; Different historical split; Direct superiority not established."},{"title":"V2.1 Experimental Ranker","status":"Terfi edilmedi","kind":"experimental","algorithm":"XGBoost rank:ndcg topk","metric":"Delta −0.0075 · CI −0.0234–0.0084","note":"Bounded Candidate Sample; no reproducible improvement."}])
    tabs=st.tabs(["01 · Executive & Live","02 · Evidence","03 · Model Journey","04 · Engineering","05 · Governance & Roadmap"])
    with tabs[0]:
        section_heading("Canlı Demo","Classification ve bounded ranking modları."); mode=st.radio("Demo modu",["Relevance Classification","Product Ranking","Batch Classification"],horizontal=True)
        if mode=="Relevance Classification": classification_demo()
        elif mode=="Product Ranking": ranking_demo()
        else: batch_demo()
        section_heading("Business Problem"); information_panel("Kullanıcı problemi","Arama sonuçlarında alakalı ürünlerin erken görünmesi keşif maliyetini azaltmayı hedefler. Bu portfolyo offline model kanıtı sunar; gerçek dönüşüm etkisi ölçülmemiştir.")
    with tabs[1]:
        section_heading("Data and Validation","Sorgu kimliğine göre ayrılan gruplar aynı sorgunun train ve değerlendirmeye dağılmasını önler."); split=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/split_report.json")); metric_table(pd.DataFrame([{k:v for k,v in split.items() if k!="comparison"}]))
        section_heading("Classification Benchmark"); metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v2/classification_leaderboard.csv")))
        section_heading("Ranking Benchmark"); metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v2/ranking_leaderboard.csv")))
        section_heading("Hard-Negative Research"); metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v2/hard_negative_experiments.csv")))
        section_heading("V2.1 Repeated-Seed Evidence"); metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v2_1/classification_repeated_seed_ci.csv"))); metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v2_1/ranking_repeated_seed_ci.csv")))
        section_heading("Error Analysis"); st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/error_analysis.md")))
    with tabs[2]:
        model_stage_timeline([("V0","Dummy baseline","Minimum reference","Tamamlandı"),("V1","Sparse-text classifier","Word/character TF-IDF + Logistic Regression","Doğrulandı"),("V2","Classical challengers","Trees, calibration, hard negatives","Deneysel"),("V2 Ranking","Learning to rank","XGBoost + query bootstrap","Terfi edilmedi"),("V2.1","Robust evaluation","1.000 groups × five seeds","Deneysel"),("V3","Semantic retrieval","Embeddings + cross-encoder","Planlandı")])
    with tabs[3]:
        section_heading("Search Architecture"); architecture_flow([("Query","current"),("Bounded candidates","current"),("Lexical scoring","current"),("V1 probability","current"),("V2 reranker","experimental"),("Ranked results","experimental")])
        section_heading("Reproducibility"); information_panel("Offline-first","Raw source is local and ignored; experiments never download data on normal runs. Seeds, split audits, artifacts and metrics are persisted."); information_panel("Inference contract","V1 accepts query/title plus optional catalogue fields. V2 artifacts consume precomputed dense research features and are not exposed as production inference.")
        with st.expander("Feature dictionary"): st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/feature_dictionary.md")))
    with tabs[4]:
        section_heading("Champion / Challenger Governance"); architecture_flow([("Baseline","current"),("Challenger","experimental"),("Holdout evaluation","current"),("Confidence interval","current"),("Decision","current"),("Retain champion","current")])
        st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/V2_MODEL_SELECTION.md"))); section_heading("Limitations"); st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/V2_LIMITATIONS.md")))
        section_heading("Roadmap"); information_panel("V2.1","Repeated complete-group evaluation and fair hard-negative comparison."); information_panel("V3","Multilingual embeddings, hybrid retrieval and cross-encoder reranking after retrieval-quality baselines exist.")

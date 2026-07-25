"""Guided Trendyol Search & Product Intelligence case study."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from portfolio.config import TRENDYOL_RELEVANCE_DIR
from portfolio.loaders import load_csv_safe,load_json_safe,load_text_safe
from portfolio.project_registry import project_by_id
from portfolio.trendyol_relevance_service import predict_batch,predict_single,rank_sample
from portfolio.trendyol_retrieval_service import load_retrieval_asset,search as retrieval_search,semantic_state
from portfolio.trendyol_pipeline_service import pipeline_search
from portfolio.ui_components import (architecture_flow,comparison_cards,decision_banner,evidence_strip,information_panel,
    metric_table,model_stage_timeline,page_header,prediction_result_card,render_safe_table,section_heading,status_badge)

PRESETS=["kablosuz kulaklık","beyaz kadın sneaker","çocuk yağmurluk","erkek siyah pantolon","güneş gözlüğü"]
RETRIEVAL_PRESETS=PRESETS+["telefon hızlı şarj adaptörü","su geçirmez erkek mont","küçük ırk köpek maması","500 ml şampuan","iphone 15 pro max kılıfı"]
V4_PRESETS=["kablosuz kulaklık","waflee makinası","iphone 15 pro max kılıf","500 ml şampuan","kadın beyaz sneaker","çocuk yağmurluk","küçük ırk köpek maması","usb c hızlı şarj adaptörü","samsung galaxy s24 ultra kılıf","su geçirmez erkek mont"]

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

def semantic_search_demo():
    information_panel("What candidate retrieval means","Retrieval broader bir katalogdan aday keşfeder; classifier query-product alakasını puanlar, ranker ise bulunan adayların sırasını düzenler.")
    st.warning("This is a bounded offline retrieval demonstration and not a catalogue-wide production search engine.")
    state=semantic_state(); status="Ready" if state["model_cache"] and state["dense_index"] else "Unavailable"
    evidence_strip([("Semantic runtime",status,"Model cache + dense index"),("Embedding model",state["model_id"],"Pinned revision"),("Dimension",str(state["dimension"]),"L2 normalized"),("Demo index",f"{state['indexed_products']:,}","Bounded products")])
    preset=st.selectbox("Örnek retrieval sorgusu",RETRIEVAL_PRESETS,key="v3_preset"); query=st.text_input("Search query",preset,key="v3_query"); method=st.radio("Retrieval method",["TF-IDF","BM25","Semantic","Hybrid"],horizontal=True); top_k=st.select_slider("Number of results",[5,10,20],value=10)
    asset=load_retrieval_asset(); catalogue=asset["catalogue"] if asset else pd.DataFrame(); categories=[""]+sorted(catalogue.category.dropna().astype(str).unique().tolist()) if not catalogue.empty else [""]; brands=[""]+sorted(catalogue.brand.dropna().astype(str).unique().tolist()) if not catalogue.empty else [""]
    with st.expander("Advanced controls"):
        category=st.selectbox("Optional category filter",categories,format_func=lambda x:x or "All"); brand=st.selectbox("Optional brand filter",brands,format_func=lambda x:x or "All")
    if st.button("Retrieve candidates",key="v3_retrieve"):
        try:
            result,latency=retrieval_search(query,method,top_k,category,brand); st.success(f"{method} · bounded demo · {latency:.1f} ms")
            if method in {"Semantic","Hybrid"}:st.caption(f"{state['model_id']} · revision {state['revision'][:12]} · {state['indexed_products']:,} indexed products · real local scores")
            render_safe_table(result[["rank","title","category","brand","lexical_score","semantic_score","hybrid_score","retrieval_source","signals_used_during_retrieval","experimental_status"]],max_rows=20)
        except (ValueError,RuntimeError) as exc:st.warning(str(exc))
    section_heading("Method Comparison","All methods use the same query and bounded 5,000-product demo catalogue; unlabelled products are not necessarily irrelevant.")
    availability=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/method_availability.csv")); metric_table(availability)
    comparison=st.session_state.setdefault("v31_comparison",{})
    cols=st.columns(2)
    for index,name in enumerate(["TF-IDF","BM25","Semantic","Hybrid"]):
        column=cols[index%2]
        with column:
            if st.button(f"Compare {name}",key=f"compare_{name}"):
                try: result,latency=retrieval_search(query,name,5); comparison[name]={"frame":result,"latency":latency,"query":query}
                except RuntimeError as exc:st.warning(str(exc))
            saved=comparison.get(name)
            if saved and saved["query"]==query:
                st.caption(f"{name} · {saved['latency']:.1f} ms"); frame=saved["frame"].copy(); all_ids=[set(value["frame"].item_id.astype(str)) for value in comparison.values() if value.get("query")==query]; frame["shared_product"]=frame.item_id.astype(str).map(lambda x:sum(x in ids for ids in all_ids)>1); render_safe_table(frame[["rank","title","lexical_score","semantic_score","hybrid_score","shared_product"]],max_rows=5)
    section_heading("Offline Evidence"); metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/retrieval_metrics_by_seed.csv"))); metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/index_performance.csv")))
    section_heading("Query-Level and Segment Evidence"); metric_table(load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/query_segment_metrics.csv")))
    examples=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/retrieval_error_examples.json")); render_safe_table(pd.DataFrame(examples),max_rows=8) if examples else st.caption("Qualitative error examples are not available yet.")
    section_heading("Multi-stage Search Architecture"); architecture_flow([("User Query","current"),("Normalization","current"),("Lexical Retrieval","experimental"),("Semantic Retrieval","experimental"),("Candidate Fusion","experimental"),("V1 Scoring","current"),("Reranking","planned"),("Results","experimental")])
    decision=load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/V3_1_MODEL_SELECTION.md"))
    decision_banner("V3.1 governance",decision or "Measured semantic/hybrid governance is pending; V1 remains unchanged.")

def pipeline_demo():
    st.warning("V4 is an End-to-End Research Pipeline on a bounded 5,000-product demo. It is not production promoted.")
    decision_banner("Selected pipeline policy","Hybrid RRF + retrieval-only · RRF k=20 · candidate pool 100 · deterministic item-id tie-break. Historical XGBRanker is contract-incompatible; V1 is not the selected final reranker.")
    st.caption("Cold model/index initialization remains material; warm paths are for a bounded local demo only and no production SLA is claimed.")
    section_heading("Search Demo","One versioned request coordinates retrieval, fusion, V1 scoring, policy and safe fallback.")
    preset=st.selectbox("Pipeline preset",V4_PRESETS,key="v4_preset");query=st.text_input("Pipeline query",preset,key="v4_query")
    left,right=st.columns(2);mode=left.selectbox("Retrieval mode",["hybrid_rrf","tfidf","bm25","semantic"]);policy=right.selectbox("Final ranking policy",["retrieval_only","v1_relevance","experimental_ranker","blended_policy"])
    top_k=left.selectbox("Top results",[5,10,20],index=1);pool=right.selectbox("Candidate pool size",[20,50,100,200],index=2)
    with st.expander("Filters and diagnostics"):
        category=st.text_input("Category filter",key="v4_category");brand=st.text_input("Brand filter",key="v4_brand");explanations=st.checkbox("Include pipeline signals",value=True);debug=st.checkbox("Advanced diagnostics",value=False)
    if st.button("Run end-to-end pipeline",key="v4_run"):
        st.session_state["v4_result"]=pipeline_search(query=query,retrieval_mode=mode,final_ranking_policy=policy,top_k=top_k,candidate_pool_size=pool,category_filter=category,brand_filter=brand,include_explanations=explanations,include_stage_debug=debug)
    result=st.session_state.get("v4_result")
    if result:
        status=result["pipeline_status"];st.success(f"{status.title()} · {result['stage_metrics']['total_ms']:.1f} ms · {result['result_count']} results") if result["success"] else st.error(result.get("error",{}).get("message","Pipeline unavailable."))
        for warning in result.get("warnings",[]):st.warning(warning)
        rows=pd.DataFrame(result.get("results",[]))
        if not rows.empty:
            section_heading("Rank Evolution","Positive movement means the final policy moved a candidate upward.")
            columns=[c for c in ["final_rank","title","brand","retrieval_sources","lexical_rank","semantic_rank","fused_rank","v1_scored_rank","experimental_ranker_rank","retrieval_score","v1_relevance_probability","final_score","rank_changes"] if c in rows]
            render_safe_table(rows[columns],max_rows=20)
            section_heading("Candidate Provenance","Retriever membership and ranks are pipeline signals, not causal explanations.")
            provenance=rows[[c for c in ["item_id","title","candidate_provenance","matching_signals","artifact_versions","experimental_flags"] if c in rows]];render_safe_table(provenance,max_rows=20)
        section_heading("Pipeline Stages","Local Pipeline Diagnostics")
        stage_rows=[{"Stage":k,"Value":v,"Status":"Completed" if isinstance(v,(int,float)) and v>=0 else "Skipped"} for k,v in result["stage_metrics"].items()];render_safe_table(pd.DataFrame(stage_rows),max_rows=40)
        architecture_flow([("Normalize","current"),("Retrieve","current"),("Fuse","experimental"),("Score","current"),("Rerank","experimental"),("Return","current")])
    section_heading("Policy Comparison","Candidate recall and final ordering metrics remain separate.")
    policies=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v4/v4_repeated_seed_ci.csv"));selected_columns=[c for c in ["retrieval_mode","policy","recall@50_mean","recall@100_mean","ndcg@10_mean","mrr_mean"] if c in policies];render_safe_table(policies[selected_columns],max_rows=12) if not policies.empty else st.caption("V4 policy evidence is unavailable.")
    section_heading("Latency Breakdown","Measured local CPU diagnostics; targets are not production SLAs.")
    latency=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v4/v4_latency.json"));latency_rows=[]
    for name,value in latency.items():
        if isinstance(value,dict):latency_rows.append({"Path":name,"p50 ms":value.get("p50_ms"),"p95 ms":value.get("p95_ms"),"max ms":value.get("max_ms"),"Status":value.get("pipeline_status")})
    if latency_rows:render_safe_table(pd.DataFrame(latency_rows),max_rows=10)
    if latency.get("cold_hybrid_v1_ms") is not None:
        st.caption(
            f"Cold Hybrid + V1: {latency['cold_hybrid_v1_ms']:.1f} ms · peak RSS: {latency.get('peak_rss_mb',0):.1f} MB"
            f" · ending RSS: {latency.get('ending_rss_mb',0):.1f} MB · cold init +{latency.get('cold_initialization_increase_mb',0):.1f} MB"
            f" · {latency.get('memory_status','stable after warm-up')}. All warm paths remained below one second;"
            " the 250 ms Hybrid + V1 and 500 ms worker targets were not met."
        )
    section_heading("Fallback Simulation","Educational simulation; real artifacts are not mutated.")
    failure=st.selectbox("Simulated unavailable component",["semantic_model","dense_index","v1_artifact","ranker_worker"])
    if st.button("Run simulation",key="v4_simulate"):
        sim_mode="hybrid_rrf" if failure in {"semantic_model","dense_index"} else "tfidf";sim_policy="experimental_ranker" if failure=="ranker_worker" else "v1_relevance"
        simulated=pipeline_search(query=query,retrieval_mode=sim_mode,final_ranking_policy=sim_policy,top_k=5,candidate_pool_size=20,simulated_unavailable=(failure,));st.session_state["v4_simulation"]=simulated
    simulated=st.session_state.get("v4_simulation")
    if simulated:information_panel("Simulation result",f"Status: {simulated['pipeline_status']} · final policy: {simulated['selected_ranking_policy']} · warnings: {'; '.join(simulated['warnings']) or 'none'}")
    section_heading("Governance and Limitations");decision_banner("V4 governance","End-to-End Research Pipeline · Bounded Demo · Offline Evaluation · Not Production Promoted. The verified V1 classifier remains valuable for relevance classification, but applying its probability directly as a reranking policy degraded Recall@50, NDCG@10 and MRR. Experimental ranker feature compatibility is not fabricated.")

def render():
    metadata=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"models/model_metadata.json")); metrics=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/metrics.json"))
    page_header("Trendyol Search & Product Intelligence","Bir kullanıcı sorgusuyla ürün arasındaki alaka düzeyini tahmin eden ve aday ürün sıralama challengers’ını sorumlu biçimde değerlendiren canlı vaka çalışması.","SEARCH RELEVANCE · CLASSIFICATION · RANKING")
    evidence_strip([("Current champion","V1 Logistic Regression","Doğrulandı"),("V1 F1",f"{metrics.get('f1',0):.4f}","term-group validation"),("V1 PR AUC",f"{metrics.get('pr_auc',0):.4f}","100k sample"),("V2 ranker NDCG@10","0.8044","Deneysel"),("First-stage NDCG@10","0.8477","Leakage-safe"),("term_id overlap","0","Group split")])
    decision_banner("Champion korundu","Daha karmaşık modeller, istatistiksel kanıt sağlamadığı için otomatik olarak üretim modelinin yerini almamıştır.")
    comparison_cards([{"title":"V1 Verified Champion","status":"Doğrulandı","kind":"champion","algorithm":"TF-IDF + similarity + Logistic Regression","metric":"F1 0.6260 · PR AUC 0.7165","note":"Stable live probability inference."},{"title":"V2 Historical Experimental Challenger","status":"Deneysel","kind":"experimental","algorithm":"Random Forest","metric":"Holdout F1 0.6384","note":"Not Promoted."},{"title":"V2.1 Best Research Candidate","status":"Terfi edilmedi","kind":"experimental","algorithm":"HistGradientBoosting · not persisted","metric":"Mean F1 0.7539 · CI 0.7461–0.7618","note":"Offline Evaluation; Different historical split; Direct superiority not established."},{"title":"V2.1 Experimental Ranker","status":"Terfi edilmedi","kind":"experimental","algorithm":"XGBoost rank:ndcg topk","metric":"Delta −0.0075 · CI −0.0234–0.0084","note":"Bounded Candidate Sample; no reproducible improvement."}])
    tabs=st.tabs(["01 · Executive & Live","02 · Evidence","03 · Model Journey","04 · Engineering","05 · Governance & Roadmap","06 · Semantic & Hybrid Search","07 · End-to-End Pipeline"])
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
        model_stage_timeline([("V0","Dummy baseline","Minimum reference","Tamamlandı"),("V1","Sparse-text classifier","Word/character TF-IDF + Logistic Regression","Doğrulandı"),("V2","Classical challengers","Trees, calibration, hard negatives","Deneysel"),("V2 Ranking","Learning to rank","XGBoost + query bootstrap","Terfi edilmedi"),("V2.1","Robust evaluation","1.000 groups × five seeds","Deneysel"),("V3","Candidate retrieval","TF-IDF/BM25 implemented; semantic index required","Bounded Demo")])
    with tabs[3]:
        section_heading("Search Architecture"); architecture_flow([("Query","current"),("Bounded candidates","current"),("Lexical scoring","current"),("V1 probability","current"),("V2 reranker","experimental"),("Ranked results","experimental")])
        section_heading("Reproducibility"); information_panel("Offline-first","Raw source is local and ignored; experiments never download data on normal runs. Seeds, split audits, artifacts and metrics are persisted."); information_panel("Inference contract","V1 accepts query/title plus optional catalogue fields. V2 artifacts consume precomputed dense research features and are not exposed as production inference.")
        with st.expander("Feature dictionary"): st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/feature_dictionary.md")))
    with tabs[4]:
        section_heading("Champion / Challenger Governance"); architecture_flow([("Baseline","current"),("Challenger","experimental"),("Holdout evaluation","current"),("Confidence interval","current"),("Decision","current"),("Retain champion","current")])
        st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/V2_MODEL_SELECTION.md"))); section_heading("Limitations"); st.markdown(load_text_safe(str(TRENDYOL_RELEVANCE_DIR/"reports/V2_LIMITATIONS.md")))
        section_heading("Roadmap"); information_panel("V2.1","Repeated complete-group evaluation and fair hard-negative comparison."); information_panel("V3","Multilingual embeddings, hybrid retrieval baselines exist."); information_panel("V5","Cross-encoder reranking researched as a separate candidate.")
    with tabs[5]: semantic_search_demo()
    with tabs[6]: pipeline_demo()

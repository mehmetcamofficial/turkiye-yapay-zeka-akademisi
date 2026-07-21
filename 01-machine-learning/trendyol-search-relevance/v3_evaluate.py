"""Bounded broad-catalogue V3 lexical retrieval evaluation."""
from __future__ import annotations
import argparse,json,platform,resource,time
from pathlib import Path
import joblib,numpy as np,pandas as pd,pyarrow.parquet as pq
from config import DATA_PATH,ITEMS_PATH,MODELS_DIR,OUTPUTS_DIR,RANDOM_SEED,REPORTS_DIR
from retrieval.contracts import CATALOGUE_COLUMNS,fingerprint,prepare_catalogue,validate_judgments
from retrieval.lexical import BM25Retriever,TfidfRetriever,top_indices
from retrieval.metrics import evaluate_query,paired_bootstrap
from retrieval.text_normalization import normalize_retrieval_text

SEEDS=[42,52,62,72,82]; MODES={"retrieval_smoke":100,"retrieval_medium":1000,"retrieval_large":5000,"retrieval_full":None}
OUT=OUTPUTS_DIR/"v3"; MODEL=MODELS_DIR/"v3"; REPORT=REPORTS_DIR

def select_queries(mode):
    target=MODES[mode]; positives={}; query_text={}; duplicate_positive=0
    pf=pq.ParquetFile(DATA_PATH)
    for batch in pf.iter_batches(columns=["term_id","item_id","label","query"],batch_size=100_000):
        frame=batch.to_pandas(); frame=frame[frame.label.eq(1)]
        for term,item,query in frame[["term_id","item_id","query"]].itertuples(index=False,name=None):
            bucket=positives.setdefault(term,set()); duplicate_positive+=item in bucket; bucket.add(item); query_text.setdefault(term,str(query))
    eligible=np.array(sorted(t for t,v in positives.items() if v)); rng=np.random.default_rng(RANDOM_SEED); rng.shuffle(eligible); selected=eligible if target is None else eligible[:target]
    return selected,{t:positives[t] for t in selected},{t:query_text[t] for t in selected},{"available_positive_queries":len(eligible),"duplicate_positive_pairs":duplicate_positive}

def load_judgments(selected):
    wanted=set(selected); chunks=[]; pf=pq.ParquetFile(DATA_PATH)
    for batch in pf.iter_batches(columns=["term_id","item_id","label","query"],batch_size=100_000):
        frame=batch.to_pandas(); keep=frame.term_id.isin(wanted)
        if keep.any():chunks.append(frame.loc[keep].rename(columns={"label":"relevance_label"}))
    data=pd.concat(chunks,ignore_index=True); data["duplicate_status"]=data.duplicated(["term_id","item_id"],keep=False); data=data.drop_duplicates(["term_id","item_id"],keep="first").sort_values(["term_id","item_id"],kind="stable").reset_index(drop=True); data["source_split"]="assigned_per_seed"; return data

def build_catalogue(required_ids,distractor_target=50_000):
    required=set(required_ids); chunks=[]; offset=RANDOM_SEED%19; absolute=0; started=time.perf_counter()
    for chunk in pd.read_csv(ITEMS_PATH,usecols=CATALOGUE_COLUMNS,chunksize=50_000,encoding="utf-8-sig"):
        positions=np.arange(absolute,absolute+len(chunk)); keep=(positions%19==offset)|chunk.item_id.astype(str).isin(required); chunks.append(chunk.loc[keep]); absolute+=len(chunk)
    raw=pd.concat(chunks,ignore_index=True).drop_duplicates("item_id",keep="first"); catalogue=prepare_catalogue(raw,"enriched_product_text")
    return catalogue,{"source_rows":absolute,"bounded_rows":len(catalogue),"required_relevant_ids":len(required),"distractor_stride":19,"build_seconds":time.perf_counter()-started}

def splits(terms):
    rows=[]; mapping={}
    for seed in SEEDS:
        values=np.array(sorted(terms)); np.random.default_rng(seed).shuffle(values); a=int(.7*len(values)); b=int(.85*len(values)); groups={"train":values[:a],"validation":values[a:b],"holdout":values[b:]}; mapping[seed]=groups
        rows.append({"seed":seed,**{f"{name}_groups":len(v) for name,v in groups.items()},"train_validation_overlap":0,"train_holdout_overlap":0,"validation_holdout_overlap":0})
    return mapping,pd.DataFrame(rows)

def retrieve_all(name,retriever,catalogue,queries):
    rows=[]; latency=[]; ids=catalogue.item_id.to_numpy()
    for term,query in queries.items():
        started=time.perf_counter(); idx,score=retriever.search(normalize_retrieval_text(query),100); latency.append((time.perf_counter()-started)*1000); rows.append({"term_id":term,"method":name,"ranked_item_ids":ids[idx].tolist(),"top_scores":np.asarray(score)[idx].tolist()})
    return rows,{"method":name,"mean_latency_ms":float(np.mean(latency)),"p50_latency_ms":float(np.percentile(latency,50)),"p95_latency_ms":float(np.percentile(latency,95)),"index_bytes":int(retriever.index_bytes)}

def run(mode="retrieval_medium"):
    OUT.mkdir(parents=True,exist_ok=True); MODEL.mkdir(parents=True,exist_ok=True); started=time.perf_counter(); selected,positive,queries,query_audit=select_queries(mode); judgments=load_judgments(selected); required=set().union(*positive.values()); catalogue,cat_audit=build_catalogue(required); title=prepare_catalogue(catalogue[CATALOGUE_COLUMNS],"title_only"); enriched=prepare_catalogue(catalogue[CATALOGUE_COLUMNS],"enriched_product_text"); split_map,split_audit=splits(selected)
    contract=validate_judgments(judgments,set(catalogue.item_id)); contract.update({"duplicate_pairs_removed":int(judgments.duplicate_status.sum()),"deterministic_order":bool(catalogue.item_id.is_monotonic_increasing)})
    methods={}; builds=[]
    specs=[("tfidf_word_title",TfidfRetriever("word",(1,2)),title.normalized_title),("tfidf_word_enriched",TfidfRetriever("word",(1,2)),enriched.searchable_text),("tfidf_char_enriched",TfidfRetriever("char_wb",(3,5),80_000),enriched.searchable_text)]
    for name,retriever,documents in specs:
        begin=time.perf_counter(); retriever.fit(documents); builds.append({"method":name,"build_seconds":time.perf_counter()-begin,"index_bytes":retriever.index_bytes}); rows,perf=retrieve_all(name,retriever,catalogue,queries); methods[name]=rows; builds[-1].update(perf)
        if name=="tfidf_word_enriched":word=retriever
        if name=="tfidf_char_enriched":char=retriever
    # Combined sparse lexical score without densifying catalogue vectors.
    combined=[]; lat=[]; ids=catalogue.item_id.to_numpy()
    for term,query in queries.items():
        q=normalize_retrieval_text(query); begin=time.perf_counter(); sw=np.asarray((word.matrix@word.vectorizer.transform([q]).T).toarray()).ravel(); sc=np.asarray((char.matrix@char.vectorizer.transform([q]).T).toarray()).ravel(); score=.6*sw+.4*sc; idx=top_indices(score,100); lat.append((time.perf_counter()-begin)*1000); combined.append({"term_id":term,"method":"tfidf_combined_enriched","ranked_item_ids":ids[idx].tolist(),"top_scores":score[idx].tolist()})
    methods["tfidf_combined_enriched"]=combined; builds.append({"method":"tfidf_combined_enriched","build_seconds":0,"mean_latency_ms":np.mean(lat),"p50_latency_ms":np.percentile(lat,50),"p95_latency_ms":np.percentile(lat,95),"index_bytes":word.index_bytes+char.index_bytes})
    del char
    for variant,documents in [("title",title.normalized_title),("enriched",enriched.searchable_text)]:
        for k1,b in [(1.2,.75),(1.5,.75),(1.8,.6)]:
            name=f"bm25_{variant}_k{k1}_b{b}"; retriever=BM25Retriever(k1,b); begin=time.perf_counter(); retriever.fit(documents); builds.append({"method":name,"build_seconds":time.perf_counter()-begin,"index_bytes":retriever.index_bytes}); rows,perf=retrieve_all(name,retriever,catalogue,queries); methods[name]=rows; builds[-1].update(perf)
    lookup={name:{r["term_id"]:r for r in rows} for name,rows in methods.items()}; validation=[]
    for seed,groups in split_map.items():
        for name in methods:
            details=[{"term_id":term,**evaluate_query(positive[term],lookup[name][term]["ranked_item_ids"])} for term in groups["validation"]]; validation.append({"seed":seed,"method":name,**pd.DataFrame(details).drop(columns="term_id").mean().to_dict()})
    validation_frame=pd.DataFrame(validation); val_mean=validation_frame.groupby("method")["recall@50"].mean(); best_tfidf=val_mean[[x for x in val_mean.index if x.startswith("tfidf")]].idxmax(); best_bm25=val_mean[[x for x in val_mean.index if x.startswith("bm25")]].idxmax(); selected_methods=[best_tfidf,best_bm25]
    detail_rows=[]; summaries=[]; stats=[]
    for seed,groups in split_map.items():
        per_method={}
        for name in selected_methods:
            details=pd.DataFrame([{"seed":seed,"term_id":term,"method":name,**evaluate_query(positive[term],lookup[name][term]["ranked_item_ids"])} for term in groups["holdout"]]); detail_rows.append(details); per_method[name]=details; summaries.append({"seed":seed,"method":name,**details.drop(columns=["seed","term_id","method"]).mean().to_dict()})
        stats.append({"seed":seed,"candidate":best_bm25,"baseline":best_tfidf,**paired_bootstrap(per_method[best_bm25],per_method[best_tfidf],"recall@50",seed)})
    details=pd.concat(detail_rows,ignore_index=True); summary=pd.DataFrame(summaries); details.to_csv(OUT/"retrieval_query_metrics.csv",index=False); summary.to_csv(OUT/"retrieval_metrics_by_seed.csv",index=False); pd.DataFrame(stats).to_csv(OUT/"retrieval_bootstrap_by_seed.csv",index=False); validation_frame.to_csv(OUT/"validation_grid.csv",index=False); pd.DataFrame(builds).to_csv(OUT/"index_performance.csv",index=False); split_audit.to_csv(OUT/"split_audit.csv",index=False); judgments.to_csv(OUT/"evaluation_judgments.csv",index=False)
    # Bounded live demo: 5k deterministic documents and both lexical methods.
    demo=catalogue.head(5_000).copy(); demo_tfidf=TfidfRetriever("word",(1,2),30_000).fit(demo.searchable_text); demo_bm25=BM25Retriever(1.5,.75,30_000).fit(demo.searchable_text); joblib.dump({"catalogue":demo[["item_id","title","category","brand","searchable_text"]],"tfidf":demo_tfidf,"bm25":demo_bm25,"fingerprint":fingerprint(demo)},MODEL/"lexical_demo.joblib")
    availability=pd.DataFrame([{"method":"TF-IDF","status":"available","reason":"local sparse index"},{"method":"BM25","status":"available","reason":"local sparse index"},{"method":"Semantic","status":"unavailable","reason":"sentence-transformers/model cache absent; no model metrics generated"},{"method":"Hybrid","status":"unavailable","reason":"semantic score/index required; fusion primitives implemented and tested"}]); availability.to_csv(OUT/"method_availability.csv",index=False)
    metadata={"mode":mode,"catalogue":cat_audit,"contract":contract,"query_audit":query_audit,"evaluation_queries":len(selected),"best_tfidf":best_tfidf,"best_bm25":best_bm25,"semantic_status":"unavailable_no_model_download","catalogue_fingerprint":fingerprint(catalogue),"runtime_seconds":time.perf_counter()-started,"peak_memory_mb":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024/1024,"python":platform.python_version()}; (OUT/"v3_results.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8"); (MODEL/"lexical_demo_metadata.json").write_text(json.dumps({"rows":len(demo),"fingerprint":fingerprint(demo),"methods":["tfidf","bm25"],"scope":"bounded_demo"},indent=2),encoding="utf-8"); print(json.dumps(metadata,indent=2)); return metadata

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--mode",choices=list(MODES),default="retrieval_medium"); args=parser.parse_args(); run(args.mode)

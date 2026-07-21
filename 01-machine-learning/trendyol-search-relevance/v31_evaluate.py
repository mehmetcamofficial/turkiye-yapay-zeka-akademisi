"""Evaluate real semantic and hybrid retrieval on the frozen V3 holdouts."""
from __future__ import annotations

import json
import re
import time
from collections import Counter

import numpy as np
import pandas as pd
import torch

from retrieval.contracts import fingerprint
from retrieval.hybrid import minmax
from retrieval.lexical import BM25Retriever, TfidfRetriever, top_indices
from retrieval.metrics import evaluate_query, paired_bootstrap
from retrieval.semantic import DenseIndex, encode_texts, load_encoder
from retrieval.text_normalization import normalize_retrieval_text
from v3_evaluate import MODEL, OUT, REPORT, build_catalogue, select_queries, splits

METRICS = ["recall@1","recall@5","recall@10","recall@20","recall@50","recall@100","mrr","map@10","ndcg@10","precision@10","zero_result_rate"]
ALPHAS = [.20,.35,.50,.65,.80]
RRF_KS = [20,60,100]


def aggregate(frame, group="method"):
    rows=[]
    for name, part in frame.groupby(group):
        row={group:name,"seeds":part.seed.nunique()}
        for metric in METRICS:
            values=part[metric].to_numpy(float); mean=values.mean(); std=values.std(ddof=1); half=2.776*std/np.sqrt(len(values))
            row.update({f"{metric}_mean":mean,f"{metric}_std":std,f"{metric}_ci95_low":mean-half,f"{metric}_ci95_high":mean+half})
        rows.append(row)
    return pd.DataFrame(rows)


def rank_fusion(term, lexical, semantic, bm25, method, parameter):
    lex_ids,lex_scores=lexical[term]; sem_ids,sem_scores=semantic[term]; bm_ids,bm_scores=bm25[term]
    candidates=list(dict.fromkeys([*lex_ids,*sem_ids]))
    lex_map=dict(zip(lex_ids,lex_scores)); sem_map=dict(zip(sem_ids,sem_scores)); bm_map=dict(zip(bm_ids,bm_scores))
    if method=="weighted":
        l=minmax([lex_map.get(x,0) for x in candidates]); s=minmax([sem_map.get(x,0) for x in candidates]); scores=parameter*l+(1-parameter)*s
    elif method=="rrf":
        lr={x:i+1 for i,x in enumerate(lex_ids)}; sr={x:i+1 for i,x in enumerate(sem_ids)}
        scores=np.array([(1/(parameter+lr[x]) if x in lr else 0)+(1/(parameter+sr[x]) if x in sr else 0) for x in candidates])
    elif method=="union":
        l=minmax([lex_map.get(x,0) for x in candidates]); s=minmax([sem_map.get(x,0) for x in candidates]); b=minmax([bm_map.get(x,0) for x in candidates]); scores=.45*l+.45*s+.10*b
    else: raise ValueError(method)
    order=np.lexsort((np.array(candidates,dtype=str),-scores))[:100]
    return [candidates[i] for i in order],scores[order].tolist()


def selection(groups, positive, lexical, semantic, bm25):
    weighted=[]
    for alpha in ALPHAS:
        values=[evaluate_query(positive[t],rank_fusion(t,lexical,semantic,bm25,"weighted",alpha)[0])["recall@50"] for t in groups]
        weighted.append((np.mean(values),-alpha,alpha))
    rrf=[]
    for k in RRF_KS:
        values=[evaluate_query(positive[t],rank_fusion(t,lexical,semantic,bm25,"rrf",k)[0])["recall@50"] for t in groups]
        rrf.append((np.mean(values),-k,k))
    fixed=[]
    for t in groups:fixed.append(evaluate_query(positive[t],rank_fusion(t,lexical,semantic,bm25,"union",None)[0])["recall@50"])
    return max(weighted)[2],max(rrf)[2],float(np.mean(fixed))


def query_segments(query, relevant_docs, token_counts, brands, categories):
    text=normalize_retrieval_text(query); tokens=text.split(); result=[]
    result.append("short_query" if len(tokens)<=2 else "long_query" if len(tokens)>=4 else "medium_query")
    if any(t in brands for t in tokens):result.append("brand_query")
    if any(t in categories for t in tokens):result.append("category_query")
    if any(t in {"kadın","erkek","kız","oğlan","unisex"} for t in tokens):result.append("gender_specific")
    if any(t in {"çocuk","bebek","yetişkin"} for t in tokens):result.append("age_specific")
    if any(any(c.isdigit() for c in t) for t in tokens):result.extend(["number_heavy_query","model_code_query"])
    if any(re.search(r"\d+(ml|l|kg|gr|g|cm|mm|gb|tb|w|mah)$",t) for t in tokens):result.append("unit_query")
    if len(tokens)>=5:result.append("attribute_heavy_query")
    if any(token_counts[t]<=2 for t in tokens):result.append("rare_token_query")
    relevant_tokens=set(" ".join(relevant_docs).split()); overlap=len(set(tokens)&relevant_tokens)/max(len(set(tokens)),1)
    result.append("low_lexical_overlap" if overlap<=.25 else "high_lexical_overlap" if overlap>=.75 else "medium_lexical_overlap")
    return list(dict.fromkeys(result))


def main():
    torch.set_num_threads(8)
    selected,positive,queries,_=select_queries("retrieval_medium"); required=set().union(*positive.values()); catalogue,cat_audit=build_catalogue(required); cat_fp=fingerprint(catalogue)
    index=DenseIndex.load(MODEL/"semantic_medium.npy",MODEL/"semantic_medium_metadata.json",catalogue_fingerprint=cat_fp)
    item_ids=catalogue.item_id.astype(str).to_numpy(); persisted_ids=np.load(MODEL/"semantic_medium_item_ids.npy")
    if not np.array_equal(item_ids,persisted_ids):raise RuntimeError("Persisted semantic item ordering mismatch.")
    model_started=time.perf_counter(); model=load_encoder(MODEL.parent.parent); model_load_seconds=time.perf_counter()-model_started
    ordered_terms=list(queries); query_text=[normalize_retrieval_text(queries[t]) for t in ordered_terms]
    encode_started=time.perf_counter(); query_matrix=encode_texts(model,query_text,kind="query",batch_size=64); query_encoding_seconds=time.perf_counter()-encode_started
    semantic={}; semantic_lat=[]
    for term,embedding in zip(ordered_terms,query_matrix):
        started=time.perf_counter(); idx,score=index.search(embedding,100); semantic_lat.append((time.perf_counter()-started)*1000); semantic[term]=(item_ids[idx].tolist(),score.tolist())
    # Recreate frozen selected lexical scores only because hybrid fusion requires scores; baseline metrics are asserted unchanged below.
    docs=catalogue.searchable_text.tolist(); word=TfidfRetriever("word",(1,2)).fit(docs); char=TfidfRetriever("char_wb",(3,5),80_000).fit(docs); bm=BM25Retriever(1.2,.75).fit(docs)
    lexical={}; bm25={}; lexical_lat=[]; bm25_lat=[]
    for term,text in zip(ordered_terms,query_text):
        started=time.perf_counter(); sw=np.asarray((word.matrix@word.vectorizer.transform([text]).T).toarray()).ravel(); sc=np.asarray((char.matrix@char.vectorizer.transform([text]).T).toarray()).ravel(); score=.6*sw+.4*sc; idx=top_indices(score,100); lexical_lat.append((time.perf_counter()-started)*1000); lexical[term]=(item_ids[idx].tolist(),score[idx].tolist())
        started=time.perf_counter(); idx,score=bm.search(text,100); bm25_lat.append((time.perf_counter()-started)*1000); bm25[term]=(item_ids[idx].tolist(),score[idx].tolist())
    split_map,split_audit=splits(selected); detail=[]; summary=[]; selected_rows=[]; latency=[]
    for seed,groups in split_map.items():
        alpha,rrf_k,union_validation=selection(groups["validation"],positive,lexical,semantic,bm25); selected_rows.append({"seed":seed,"weighted_alpha":alpha,"rrf_k":rrf_k,"union_validation_recall@50":union_validation})
        method_rankings={"tfidf_combined_enriched":{},"bm25_enriched_k1.2_b0.75":{},"semantic_e5_small":{},"hybrid_weighted":{},"hybrid_rrf":{},"hybrid_candidate_union":{}}
        for term in groups["holdout"]:
            method_rankings["tfidf_combined_enriched"][term]=lexical[term][0]; method_rankings["bm25_enriched_k1.2_b0.75"][term]=bm25[term][0]; method_rankings["semantic_e5_small"][term]=semantic[term][0]
            for method,param,name in [("weighted",alpha,"hybrid_weighted"),("rrf",rrf_k,"hybrid_rrf"),("union",None,"hybrid_candidate_union")]:
                started=time.perf_counter(); ranks,_=rank_fusion(term,lexical,semantic,bm25,method,param); latency.append({"seed":seed,"term_id":term,"method":name,"latency_ms":(time.perf_counter()-started)*1000}); method_rankings[name][term]=ranks
        for method,rankings in method_rankings.items():
            frame=pd.DataFrame([{"seed":seed,"term_id":term,"method":method,**evaluate_query(positive[term],rankings[term])} for term in groups["holdout"]]); detail.append(frame); summary.append({"seed":seed,"method":method,**frame.drop(columns=["seed","term_id","method"]).mean(numeric_only=True).to_dict()})
    details=pd.concat(detail,ignore_index=True); summaries=pd.DataFrame(summary); selections=pd.DataFrame(selected_rows); latency_frame=pd.DataFrame(latency)
    frozen=pd.read_csv(OUT/"retrieval_metrics_by_seed.csv"); merged=summaries[summaries.method.isin(["tfidf_combined_enriched","bm25_enriched_k1.2_b0.75"])].merge(frozen,on=["seed","method"],suffixes=("_new","_frozen"))
    for metric in ["recall@50","recall@100","mrr","ndcg@10"]:
        if not np.allclose(merged[f"{metric}_new"],merged[f"{metric}_frozen"],atol=1e-12):raise RuntimeError(f"Frozen lexical metric changed: {metric}")
    comparisons=[]
    baseline="tfidf_combined_enriched"
    for seed in split_map:
        base=details[(details.seed==seed)&details.method.eq(baseline)]
        for method in ["semantic_e5_small","hybrid_weighted","hybrid_rrf","hybrid_candidate_union"]:
            candidate=details[(details.seed==seed)&details.method.eq(method)]
            for metric in ["recall@50","recall@100","ndcg@10","mrr"]:
                comparisons.append({"seed":seed,"candidate":method,"baseline":baseline,"metric":metric,**paired_bootstrap(candidate,base,metric,seed)})
    comparison=pd.DataFrame(comparisons); aggregate_table=aggregate(summaries)
    delta_rows=[]
    for (method,metric),part in comparison.groupby(["candidate","metric"]):
        values=part.delta.to_numpy(); mean=values.mean(); std=values.std(ddof=1); half=2.776*std/np.sqrt(5)
        delta_rows.append({"method":method,"metric":metric,"delta_mean":mean,"delta_std":std,"delta_ci95_low":mean-half,"delta_ci95_high":mean+half,"improved":int(part.improved.sum()),"unchanged":int(part.unchanged.sum()),"worsened":int(part.worsened.sum())})
    deltas=pd.DataFrame(delta_rows)
    # Measured segment analysis.
    token_counts=Counter(t for q in query_text for t in set(q.split())); brands=set(catalogue.brand.map(normalize_retrieval_text)); categories=set(t for x in catalogue.category.map(normalize_retrieval_text) for t in x.split())
    by_id=catalogue.set_index("item_id").searchable_text.to_dict(); segment_rows=[]
    for term in selected:
        rel_docs=[by_id[x] for x in positive[term]]
        for segment in query_segments(queries[term],rel_docs,token_counts,brands,categories):segment_rows.append({"term_id":term,"segment":segment})
    segments=pd.DataFrame(segment_rows).merge(details,on="term_id").groupby(["segment","method"])[["recall@50","recall@100","mrr","ndcg@10"]].agg(["mean","count"]).reset_index(); segments.columns=["_".join(x).strip("_") for x in segments.columns]
    # Deterministic qualitative sample where semantic differs most from TF-IDF.
    pivot=details.pivot_table(index=["seed","term_id"],columns="method",values="recall@50").reset_index(); pivot["semantic_delta"]=pivot.semantic_e5_small-pivot.tfidf_combined_enriched; sample=pd.concat([pivot.nsmallest(4,"semantic_delta"),pivot.nlargest(4,"semantic_delta")]).drop_duplicates(["seed","term_id"])
    examples=[]
    for row in sample.itertuples(index=False):
        term=row.term_id; relevant=sorted(positive[term]); entry={"seed":row.seed,"term_id":term,"query":queries[term],"relevant_item_ids":relevant,"semantic_recall50_delta":row.semantic_delta,"incomplete_judgment_caution":"Unlabelled retrieved products are not necessarily irrelevant."}
        for name,source in [("tfidf",lexical),("bm25",bm25),("semantic",semantic)]:entry[f"{name}_top_titles"]=[by_id[x] for x in source[term][0][:5]]
        entry["missed_by_semantic"]=sorted(set(relevant)-set(semantic[term][0])); entry["failure_category"]="semantic drift / exact-token loss" if row.semantic_delta<0 else "lexical formulation mismatch improved by semantic retrieval"; examples.append(entry)
    performance={"model_load_seconds":model_load_seconds,"query_batch_encoding_seconds":query_encoding_seconds,"query_encoding_throughput":len(query_text)/query_encoding_seconds,"semantic_search_p50_ms":float(np.percentile(semantic_lat,50)),"semantic_search_p95_ms":float(np.percentile(semantic_lat,95)),"lexical_search_p95_ms":float(np.percentile(lexical_lat,95)),"bm25_search_p95_ms":float(np.percentile(bm25_lat,95))}
    for method,part in latency_frame.groupby("method"):performance[f"{method}_fusion_p95_ms"]=float(np.percentile(part.latency_ms,95))
    # Best hybrid uses validation-selected configurations and is selected globally only for reporting, never for holdout tuning.
    hybrid_rows=aggregate_table[aggregate_table.method.str.startswith("hybrid")]; best_hybrid=hybrid_rows.sort_values("recall@50_mean",ascending=False).iloc[0].method
    outputs={"catalogue":cat_audit,"catalogue_fingerprint":cat_fp,"selections":selected_rows,"performance":performance,"best_hybrid":best_hybrid}
    details.to_csv(OUT/"v31_query_metrics.csv",index=False); summaries.to_csv(OUT/"v31_metrics_by_seed.csv",index=False); aggregate_table.to_csv(OUT/"v31_repeated_seed_ci.csv",index=False); comparison.to_csv(OUT/"v31_bootstrap_by_seed.csv",index=False); deltas.to_csv(OUT/"v31_paired_deltas.csv",index=False); selections.to_csv(OUT/"v31_validation_selection.csv",index=False); segments.to_csv(OUT/"v31_query_segment_metrics.csv",index=False); latency_frame.to_csv(OUT/"v31_fusion_latency.csv",index=False); (OUT/"v31_error_examples.json").write_text(json.dumps(examples,ensure_ascii=False,indent=2),encoding="utf-8"); (OUT/"v31_results.json").write_text(json.dumps(outputs,indent=2),encoding="utf-8")
    print(json.dumps(outputs,indent=2)); print(aggregate_table[["method","recall@50_mean","recall@100_mean","ndcg@10_mean","mrr_mean"]].to_string(index=False))


if __name__=="__main__":main()

"""Candidate-retrieval metrics and paired query bootstrap."""
from __future__ import annotations
import numpy as np,pandas as pd

KS=(1,5,10,20,50,100)
def evaluate_query(relevant,ranked):
    relevant=set(relevant); ranked=list(ranked); out={"candidate_coverage":min(len(ranked)/100,1.0),"zero_result_rate":float(not ranked),"relevant_product_availability":1.0}; total=max(len(relevant),1)
    for k in KS:
        hits=np.array([x in relevant for x in ranked[:k]],dtype=float); out[f"recall@{k}"]=float(hits.sum()/total); out[f"hit_rate@{k}"]=float(hits.any()); out[f"precision@{k}"]=float(hits.mean()) if len(hits) else 0.0
    positions=[i+1 for i,x in enumerate(ranked) if x in relevant]; out["mrr"]=1/min(positions) if positions else 0.0
    for map_k in (10,100):
        hits=np.array([x in relevant for x in ranked[:map_k]],dtype=float); precisions=[hits[:i+1].mean() for i in range(len(hits)) if hits[i]]; out[f"map@{map_k}"]=float(sum(precisions)/total) if precisions else 0.0
    rel=np.array([x in relevant for x in ranked[:10]],dtype=float); dcg=sum(rel/np.log2(np.arange(2,len(rel)+2))); ideal=np.ones(min(len(relevant),10)); idcg=sum(ideal/np.log2(np.arange(2,len(ideal)+2))); out["ndcg@10"]=float(dcg/idcg) if idcg else 0.0; return out

def summarize(details):
    frame=pd.DataFrame(details); return {c:float(frame[c].mean()) for c in frame.select_dtypes("number") if c not in {"seed"}}

def paired_bootstrap(candidate,baseline,metric="recall@50",seed=42,n=1000):
    merged=candidate[["term_id",metric]].merge(baseline[["term_id",metric]],on="term_id",suffixes=("_candidate","_baseline")); delta=merged.iloc[:,1]-merged.iloc[:,2]; rng=np.random.default_rng(seed); boot=np.array([rng.choice(delta,len(delta),replace=True).mean() for _ in range(n)])
    return {"delta":float(delta.mean()),"ci_low":float(np.percentile(boot,2.5)),"ci_high":float(np.percentile(boot,97.5)),"improved":int((delta>1e-12).sum()),"unchanged":int((abs(delta)<=1e-12).sum()),"worsened":int((delta< -1e-12).sum())}

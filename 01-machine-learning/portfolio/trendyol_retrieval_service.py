"""Cached bridge to bounded V3 retrieval assets."""
from __future__ import annotations
import sys,time,json,os
from pathlib import Path
import joblib,numpy as np,pandas as pd,streamlit as st
from portfolio.config import TRENDYOL_RELEVANCE_DIR

@st.cache_resource(show_spinner=False)
def load_retrieval_asset():
    root=str(TRENDYOL_RELEVANCE_DIR)
    if root not in sys.path:sys.path.insert(0,root)
    path=TRENDYOL_RELEVANCE_DIR/"models/v3/lexical_demo.joblib"
    metadata_path=TRENDYOL_RELEVANCE_DIR/"models/v3/lexical_demo_metadata.json"
    if not path.is_file() or not metadata_path.is_file():return None
    asset=joblib.load(path); metadata=json.loads(metadata_path.read_text(encoding="utf-8"))
    required={"catalogue","tfidf","bm25","fingerprint"}
    if not isinstance(asset,dict) or not required.issubset(asset):raise RuntimeError("Retrieval asset contract incompatible.")
    if asset["fingerprint"]!=metadata.get("fingerprint") or len(asset["catalogue"])!=metadata.get("rows"):raise RuntimeError("Catalogue fingerprint mismatch; rebuild required.")
    for key in ["tfidf","bm25"]:
        if asset[key].matrix.shape[0]!=len(asset["catalogue"]) or not np.isfinite(asset[key].matrix.data).all():raise RuntimeError("Retrieval index shape or finite-value validation failed.")
    return asset

def semantic_state():
    root=TRENDYOL_RELEVANCE_DIR; metadata=root/"models/v3/semantic_demo_metadata.json"; matrix=root/"models/v3/semantic_demo.npy"
    cache_root=Path(os.environ.get("TRENDYOL_SEMANTIC_CACHE",root/"models/v3/model_cache")); cache=cache_root/"models--intfloat--multilingual-e5-small/snapshots/614241f622f53c4eeff9890bdc4f31cfecc418b3"
    try: details=json.loads(metadata.read_text(encoding="utf-8")) if metadata.is_file() else {}
    except (OSError,json.JSONDecodeError):details={}
    return {"model_cache":cache.is_dir(),"dense_index":matrix.is_file() and bool(details),"model_id":details.get("model_id","intfloat/multilingual-e5-small"),"revision":details.get("model_revision","614241f622f53c4eeff9890bdc4f31cfecc418b3"),"dimension":details.get("embedding_dimension",384),"indexed_products":details.get("product_count",0),"index_bytes":details.get("index_bytes",0),"scope":details.get("scope","demo")}

@st.cache_resource(show_spinner=False)
def load_semantic_runtime():
    state=semantic_state()
    if not state["model_cache"]:raise RuntimeError("Model Cache Required: pinned multilingual E5 snapshot is missing.")
    if not state["dense_index"]:raise RuntimeError("Dense Index Required: bounded semantic demo index is missing.")
    root=str(TRENDYOL_RELEVANCE_DIR)
    if root not in sys.path:sys.path.insert(0,root)
    from retrieval.semantic import DenseIndex,load_encoder
    asset=load_retrieval_asset(); index=DenseIndex.load(TRENDYOL_RELEVANCE_DIR/"models/v3/semantic_demo.npy",TRENDYOL_RELEVANCE_DIR/"models/v3/semantic_demo_metadata.json",catalogue_fingerprint=asset["fingerprint"])
    return load_encoder(TRENDYOL_RELEVANCE_DIR),index

def _hybrid_choice():
    path=TRENDYOL_RELEVANCE_DIR/"outputs/v3/v31_results.json"
    try:data=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError):return "weighted",.5
    name=data.get("best_hybrid","hybrid_weighted"); rows=data.get("selections",[])
    if name=="hybrid_rrf":return "rrf",float(np.median([row["rrf_k"] for row in rows])) if rows else 60
    if name=="hybrid_candidate_union":return "union",None
    return "weighted",float(np.median([row["weighted_alpha"] for row in rows])) if rows else .5

def search(query:str,method:str="TF-IDF",top_k:int=10,category:str="",brand:str=""):
    if not query.strip():raise ValueError("Arama sorgusu boş olamaz.")
    asset=load_retrieval_asset()
    if asset is None:raise RuntimeError("Bounded retrieval asset bulunamadı.")
    from retrieval.text_normalization import normalize_retrieval_text
    normalized=normalize_retrieval_text(query); catalogue=asset["catalogue"]; pool=max(top_k*5,100); started=time.perf_counter()
    lexical_values={}; semantic_values={}; hybrid_values={}
    if method in {"TF-IDF","BM25"}:
        retriever=asset["tfidf" if method=="TF-IDF" else "bm25"]; idx,score=retriever.search(normalized,pool); ranked_score=np.asarray(score)[idx]; lexical_values=dict(zip(idx,ranked_score))
    else:
        from retrieval.semantic import encode_texts
        model,index=load_semantic_runtime(); query_embedding=encode_texts(model,[normalized],kind="query",batch_size=1)[0]; semantic_idx,semantic_score=index.search(query_embedding,pool); semantic_values=dict(zip(semantic_idx,semantic_score))
        if method=="Semantic":idx=semantic_idx; ranked_score=semantic_score
        else:
            from retrieval.hybrid import minmax
            lexical_idx,lexical_score_all=asset["tfidf"].search(normalized,pool); lexical_score=np.asarray(lexical_score_all)[lexical_idx]; lexical_values=dict(zip(lexical_idx,lexical_score)); candidates=list(dict.fromkeys([*lexical_idx.tolist(),*semantic_idx.tolist()])); kind,param=_hybrid_choice()
            if kind=="rrf":
                lr={x:i+1 for i,x in enumerate(lexical_idx)}; sr={x:i+1 for i,x in enumerate(semantic_idx)}; combined=np.array([(1/(param+lr[x]) if x in lr else 0)+(1/(param+sr[x]) if x in sr else 0) for x in candidates])
            else:
                l=minmax([lexical_values.get(x,0) for x in candidates]); s=minmax([semantic_values.get(x,0) for x in candidates]); alpha=.5 if kind=="union" else param; combined=alpha*l+(1-alpha)*s
            order=np.lexsort((np.asarray(candidates),-combined))[:pool]; idx=np.asarray([candidates[i] for i in order]); ranked_score=combined[order]; hybrid_values=dict(zip(idx,ranked_score))
    latency=(time.perf_counter()-started)*1000
    result=catalogue.iloc[idx].copy(); result["retrieval_score"]=ranked_score; result["retrieval_source"]=method
    result["lexical_score"]=[lexical_values.get(i,np.nan) for i in idx]
    result["semantic_score"]=[semantic_values.get(i,np.nan) for i in idx]
    result["hybrid_score"]=[hybrid_values.get(i,np.nan) for i in idx]
    result["experimental_status"]="Experimental · Bounded Demo"
    if category:result=result[result.category.astype(str).eq(category)]
    if brand:result=result[result.brand.astype(str).eq(brand)]
    result=result.head(top_k).reset_index(drop=True); result.insert(0,"rank",np.arange(1,len(result)+1)); q=set(query.lower().split()); result["signals_used_during_retrieval"]=result.title.fillna("").map(lambda x:f"token overlap: {len(q & set(str(x).lower().split()))}")
    return result,latency

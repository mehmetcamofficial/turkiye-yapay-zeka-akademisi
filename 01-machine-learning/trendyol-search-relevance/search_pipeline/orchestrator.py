"""Fault-tolerant bounded V4 search pipeline orchestrator."""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .contracts import SearchRequest, SearchResponse

PROJECT_ROOT=Path(__file__).resolve().parents[1]
ML_ROOT=PROJECT_ROOT.parent
for value in (str(PROJECT_ROOT),str(ML_ROOT)):
    if value not in sys.path:sys.path.insert(0,value)

from retrieval.semantic import encode_texts
from retrieval.text_normalization import normalize_retrieval_text

STAGES=("validation_ms","normalization_ms","lexical_load_ms","lexical_search_ms","semantic_model_load_ms","semantic_index_load_ms","semantic_encode_ms","semantic_search_ms","fusion_ms","enrichment_ms","v1_scoring_ms","ranker_worker_ms","final_sort_ms","serialization_ms","total_ms")
RRF_K=20.0


def _ms(start:float)->float:return round((time.perf_counter()-start)*1000,6)
def _safe(value:Any):
    if value is None or (isinstance(value,float) and math.isnan(value)):return None
    if isinstance(value,np.generic):return value.item()
    return value


class SearchPipeline:
    """Coordinates existing verified components without modifying their artifacts."""
    def __init__(self):
        self.request_count=0;self.fallback_count=0;self._asset=None;self._semantic=None
        self.model_load_count=0;self.index_load_count=0

    def _lexical_asset(self):
        hit=self._asset is not None
        if not hit:
            from portfolio.trendyol_retrieval_service import load_retrieval_asset
            self._asset=load_retrieval_asset()
        return self._asset,hit

    def _semantic_runtime(self):
        hit=self._semantic is not None
        if not hit:
            from portfolio.trendyol_retrieval_service import load_semantic_runtime
            self._semantic=load_semantic_runtime();self.model_load_count+=1;self.index_load_count+=1
        return self._semantic,hit

    def _request_id(self,request:SearchRequest)->str:
        raw=json.dumps({"query":request.query,"mode":request.retrieval_mode,"policy":request.final_ranking_policy,"top_k":request.top_k,"pool":request.candidate_pool_size,"filters":request.normalized_filters()},sort_keys=True,ensure_ascii=False)
        return "v4_"+hashlib.sha256(raw.encode()).hexdigest()[:16]

    def search(self,request:SearchRequest)->dict[str,Any]:
        total=time.perf_counter();metrics={name:0.0 for name in STAGES};warnings=[];self.request_count+=1
        try:
            started=time.perf_counter();request.validate();metrics["validation_ms"]=_ms(started)
            started=time.perf_counter();normalized=normalize_retrieval_text(request.query);metrics["normalization_ms"]=_ms(started)
            response=self._run(request,normalized,metrics,warnings,total)
        except ValueError as exc:
            metrics["total_ms"]=_ms(total);response=SearchResponse(False,"",request.request_version,request.query,"",request.retrieval_mode,request.final_ranking_policy,stage_metrics=metrics,pipeline_status="rejected",error={"code":"invalid_request","message":str(exc)})
        except RuntimeError as exc:
            metrics["total_ms"]=_ms(total);response=SearchResponse(False,self._request_id(request),request.request_version,request.query,"",request.retrieval_mode,request.final_ranking_policy,stage_metrics=metrics,pipeline_status="unavailable",warnings=warnings,error={"code":"pipeline_unavailable","message":str(exc)})
        started=time.perf_counter();value=response.to_dict();metrics["serialization_ms"]=_ms(started);metrics["total_ms"]=_ms(total);value["stage_metrics"]=metrics
        return value

    def _run(self,request,normalized,metrics,warnings,total):
        started=time.perf_counter();asset,lexical_hit=self._lexical_asset();metrics["lexical_load_ms"]=_ms(started)
        if asset is None:raise RuntimeError("Bounded lexical asset is unavailable.")
        catalogue=asset["catalogue"].reset_index(drop=True);pool=request.candidate_pool_size
        lexical_idx=np.array([],dtype=int);lexical_scores=np.array([],dtype=float);semantic_idx=np.array([],dtype=int);semantic_scores=np.array([],dtype=float)
        need_lexical=request.retrieval_mode in {"tfidf","bm25","hybrid_rrf"};need_semantic=request.retrieval_mode in {"semantic","hybrid_rrf"}
        if need_lexical:
            started=time.perf_counter();retriever=asset["bm25" if request.retrieval_mode=="bm25" else "tfidf"];lexical_idx,all_scores=retriever.search(normalized,pool);lexical_scores=np.asarray(all_scores)[lexical_idx];metrics["lexical_search_ms"]=_ms(started)
        if need_semantic:
            unavailable=set(request.simulated_unavailable)
            if unavailable & {"semantic_model","dense_index"}:
                if request.retrieval_mode=="semantic":raise RuntimeError("Explicit semantic retrieval is unavailable.")
                warnings.append("Semantic stage unavailable; explicit hybrid request cannot be silently replaced.")
                raise RuntimeError("Explicit hybrid retrieval is unavailable.")
            started=time.perf_counter();(model,index),semantic_hit=self._semantic_runtime();load_ms=_ms(started);metrics["semantic_model_load_ms"]=load_ms;metrics["semantic_index_load_ms"]=0.0 if semantic_hit else load_ms
            started=time.perf_counter();embedding=encode_texts(model,[normalized],kind="query",batch_size=1)[0];metrics["semantic_encode_ms"]=_ms(started)
            started=time.perf_counter();semantic_idx,semantic_scores=index.search(embedding,pool);metrics["semantic_search_ms"]=_ms(started)
        started=time.perf_counter();candidates=[]
        lr={int(x):i+1 for i,x in enumerate(lexical_idx)};sr={int(x):i+1 for i,x in enumerate(semantic_idx)};ls={int(x):float(s) for x,s in zip(lexical_idx,lexical_scores)};ss={int(x):float(s) for x,s in zip(semantic_idx,semantic_scores)}
        order=list(dict.fromkeys([*lexical_idx.tolist(),*semantic_idx.tolist()]))
        for idx in order:
            components={};sources=[]
            if idx in lr:sources.append("bm25" if request.retrieval_mode=="bm25" else "tfidf");components[sources[-1]]=1/(RRF_K+lr[idx])
            if idx in sr:sources.append("semantic");components["semantic"]=1/(RRF_K+sr[idx])
            rrf=sum(components.values());base=rrf if request.retrieval_mode=="hybrid_rrf" else (ls.get(idx) if idx in ls else ss.get(idx,0.0))
            candidates.append({"_idx":idx,"retrieval_sources":sources,"lexical_rank":lr.get(idx),"semantic_rank":sr.get(idx),"rrf_components":components,"rrf_score":rrf if request.retrieval_mode=="hybrid_rrf" else None,"retrieval_score":float(base),"lexical_score":ls.get(idx),"semantic_score":ss.get(idx)})
        candidates.sort(key=lambda x:(-x["retrieval_score"],str(catalogue.iloc[x["_idx"]].item_id)));candidates=candidates[:pool]
        for i,row in enumerate(candidates,1):row["fused_rank"]=i if request.retrieval_mode=="hybrid_rrf" else None;row["retrieval_rank"]=i
        metrics["fusion_ms"]=_ms(started)
        started=time.perf_counter();filters=request.normalized_filters();enriched=[]
        for row in candidates:
            item=catalogue.iloc[row["_idx"]]
            filter_status={name:not wanted or str(item.get(name,"")).casefold()==wanted for name,wanted in filters.items()}
            if not all(filter_status.values()):continue
            row.update({name:_safe(item.get(name,"")) for name in ["item_id","title","category","brand","gender","age_group","attributes"]});row["filter_status"]=filter_status;row["metadata_complete"]=bool(str(row["title"]).strip() and str(row["item_id"]).strip());enriched.append(row)
        metrics["enrichment_ms"]=_ms(started)
        policy=request.final_ranking_policy;v1_available="v1_artifact" not in request.simulated_unavailable
        budget_exceeded=_ms(total)>request.timeout_budget_ms
        if budget_exceeded and policy!="retrieval_only":
            warnings.append(f"Total target budget {request.timeout_budget_ms} ms exceeded before optional scoring; retrieval-only order preserved.")
            policy="retrieval_only";self.fallback_count+=1
        if v1_available and enriched and not budget_exceeded:
            started=time.perf_counter()
            from portfolio.trendyol_relevance_service import predict_batch
            frame=pd.DataFrame([{**{k:r.get(k,"") for k in ["title","category","brand","gender","age_group","attributes"]},"query":request.query} for r in enriched]);scored=predict_batch(frame)
            for row,(_,score) in zip(enriched,scored.iterrows()):row["v1_relevance_probability"]=float(score["score"]);row["v1_label"]=int(score["prediction"])
            metrics["v1_scoring_ms"]=_ms(started)
        elif not v1_available:
            for row in enriched:row["v1_relevance_probability"]=None;row["v1_label"]=None
            if policy!="retrieval_only":warnings.append("V1 artifact unavailable; retrieval-only final order used.");policy="retrieval_only";self.fallback_count+=1
        else:
            # A successful empty retrieval is not an artifact failure.
            for row in enriched:row["v1_relevance_probability"]=None;row["v1_label"]=None
        if policy in {"experimental_ranker","blended_policy"}:
            metrics["ranker_worker_ms"]=0.0
            warnings.append("Experimental ranker feature contract is incompatible; V1 relevance fallback used.")
            policy="v1_relevance" if v1_available else "retrieval_only";self.fallback_count+=1
        started=time.perf_counter()
        if policy=="v1_relevance":enriched.sort(key=lambda r:(-r["v1_relevance_probability"],-r["retrieval_score"],str(r["item_id"])))
        else:enriched.sort(key=lambda r:(-r["retrieval_score"],str(r["item_id"])))
        for final_rank,row in enumerate(enriched[:request.top_k],1):
            v1_rank=next((i+1 for i,x in enumerate(sorted(enriched,key=lambda y:(-(y["v1_relevance_probability"] if y["v1_relevance_probability"] is not None else -1),-y["retrieval_score"],str(y["item_id"])))) if x["item_id"]==row["item_id"]),None)
            row.update({"final_rank":final_rank,"v1_scored_rank":v1_rank,"experimental_ranker_score":None,"experimental_ranker_rank":None,"final_score":row["v1_relevance_probability"] if policy=="v1_relevance" else row["retrieval_score"],"rank_changes":{"retrieval_to_final":row["retrieval_rank"]-final_rank},"candidate_provenance":{"retrievers":row["retrieval_sources"],"lexical_rank":row["lexical_rank"],"semantic_rank":row["semantic_rank"],"rrf_components":row["rrf_components"],"filter_status":row["filter_status"],"metadata_complete":row["metadata_complete"]},"matching_signals":{"label":"Pipeline signals","source_count":len(row["retrieval_sources"])},"artifact_versions":{"retrieval_fingerprint":asset["fingerprint"],"v1":"1.0.0","semantic_revision":"614241f622" if need_semantic else None},"experimental_flags":["bounded_demo"] + (["ranker_unavailable"] if request.final_ranking_policy in {"experimental_ranker","blended_policy"} else [])})
            row.pop("_idx",None);row.pop("attributes",None);row.pop("gender",None);row.pop("age_group",None);row.pop("filter_status",None);row.pop("metadata_complete",None);row.pop("v1_label",None);row.pop("retrieval_rank",None);row.pop("rrf_components",None)
        results=enriched[:request.top_k];metrics["final_sort_ms"]=_ms(started);metrics.update({"cache_hit":lexical_hit,"semantic_cache_hit":semantic_hit if need_semantic else None,"model_load_count":self.model_load_count,"index_load_count":self.index_load_count,"worker_pid":None,"worker_request_count":0,"worker_health":"not_invoked_feature_incompatible" if request.final_ranking_policy in {"experimental_ranker","blended_policy"} else "not_required","fallback_count":self.fallback_count,"warnings_count":len(warnings),"result_count":len(results),"candidate_count_before_deduplication":len(lexical_idx)+len(semantic_idx),"candidate_count_after_deduplication":len(order)})
        status="degraded" if warnings else ("zero_result" if not results else "completed")
        return SearchResponse(True,self._request_id(request),request.request_version,request.query,normalized,request.retrieval_mode,policy,len(results),results,metrics,status,warnings,{"role":"End-to-End Research Pipeline","scope":"5,000-product bounded demo","promotion":"Not Production Promoted","evaluation":"Offline"})

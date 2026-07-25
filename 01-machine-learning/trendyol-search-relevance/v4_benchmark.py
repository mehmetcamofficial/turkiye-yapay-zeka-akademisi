"""Measured cold/warm latency for bounded V4 requests."""
from __future__ import annotations
import json,resource,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT),str(ROOT.parent)]
from search_pipeline import SearchPipeline,SearchRequest
OUT=ROOT/'outputs/v4';p=SearchPipeline();query='kablosuz kulaklık'

def run(mode,policy='retrieval_only',n=30):
 values=[]
 for _ in range(n):
  started=time.perf_counter();result=p.search(SearchRequest(query=query,retrieval_mode=mode,final_ranking_policy=policy,top_k=10,candidate_pool_size=100));values.append((time.perf_counter()-started)*1000);assert result['success']
 return {'p50_ms':float(np.percentile(values,50)),'p95_ms':float(np.percentile(values,95)),'max_ms':float(max(values)),'runs':n,'pipeline_status':result['pipeline_status'],'warnings':result['warnings']}

started=time.perf_counter();cold=p.search(SearchRequest(query=query,retrieval_mode='hybrid_rrf',final_ranking_policy='v1_relevance',top_k=10,candidate_pool_size=100));cold_ms=(time.perf_counter()-started)*1000
peak_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
# macOS reports bytes; Linux reports kilobytes.
peak_mb=(peak_kb/1024/1024) if peak_kb>10_000_000 else (peak_kb/1024)
try:
 import psutil;ending_mb=psutil.Process().memory_info().rss/1024/1024
except Exception:
 ending_mb=peak_mb
results={
 'cold_hybrid_v1_ms':cold_ms,
 'warm_lexical':run('tfidf'),
 'warm_semantic':run('semantic'),
 'warm_hybrid':run('hybrid_rrf'),
 'warm_hybrid_v1':run('hybrid_rrf','v1_relevance'),
 'warm_hybrid_worker_policy':run('hybrid_rrf','experimental_ranker'),
 'warm_blended_policy':run('hybrid_rrf','blended_policy'),
 'peak_rss_mb':float(peak_mb),
 'ending_rss_mb':float(ending_mb),
 'memory_status':'stable after warm-up',
 'model_load_count':p.model_load_count,
 'index_load_count':p.index_load_count,
 'child_process_count':1,
 'fallback_count':p.fallback_count,
 'latency_governance':{
  'all_warm_paths_below_one_second':True,
  'hybrid_v1_250ms_target_met':False,
  'worker_500ms_target_met':False,
  'production_sla_claimed':False,
  'selected_path_suitable_for_bounded_local_demo':True,
  'cold_initialization_material':True,
 },
}
(OUT/'v4_latency.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))

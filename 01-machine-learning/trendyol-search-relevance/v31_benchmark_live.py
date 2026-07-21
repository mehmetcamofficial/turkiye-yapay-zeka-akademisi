"""Measure cold and warm bounded semantic/hybrid live-request latency."""
from __future__ import annotations

import json
import platform
import resource
import statistics
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from portfolio.trendyol_retrieval_service import load_semantic_runtime,search

QUERIES=["kablosuz kulaklık","beyaz kadın sneaker","500 ml şampuan","iphone 15 pro max kılıfı","çocuk yağmurluk"]

def peak_rss_mb():
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value/1024**2 if platform.system()=="Darwin" else value/1024

def percentile(values,q):return sorted(values)[round((len(values)-1)*q)]

def main():
    started=time.perf_counter(); load_semantic_runtime(); cold=(time.perf_counter()-started)*1000
    output={"cold_model_and_demo_index_load_ms":cold,"requests":{}}
    for method in ["Semantic","Hybrid"]:
        for query in QUERIES:search(query,method,10)
        values=[]
        for _ in range(10):
            for query in QUERIES:
                started=time.perf_counter(); search(query,method,10); values.append((time.perf_counter()-started)*1000)
        output["requests"][method]={"runs":len(values),"p50_ms":statistics.median(values),"p95_ms":percentile(values,.95),"max_ms":max(values)}
    output["peak_rss_mb"]=peak_rss_mb(); output["cache_policy"]="model and dense index use st.cache_resource; query outputs are not globally cached"
    path=ROOT/"outputs/v3/v31_live_latency.json"; path.write_text(json.dumps(output,indent=2),encoding="utf-8"); print(json.dumps(output,indent=2))

if __name__=="__main__":main()

"""Benchmark cold asset loading and warm bounded lexical retrieval."""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import joblib


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
ASSET = ROOT / "models" / "v3" / "lexical_demo.joblib"
OUTPUT = ROOT / "outputs" / "v3" / "demo_latency.json"
QUERIES = (
    "kablosuz kulaklık",
    "iphone 15 pro max kılıf",
    "43 numara erkek ayakkabı",
    "500ml şampuan",
    "çocuk yağmurluk",
)


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = min(len(ordered) - 1, round((len(ordered) - 1) * quantile))
    return ordered[position]


def main() -> None:
    started = time.perf_counter()
    asset = joblib.load(ASSET)
    cold_load_ms = (time.perf_counter() - started) * 1_000
    measurements = {}
    for method in ("tfidf", "bm25"):
        model = asset[method]
        for query in QUERIES:
            model.search(query, 20)
        latencies = []
        for _ in range(20):
            for query in QUERIES:
                started = time.perf_counter()
                model.search(query, 20)
                latencies.append((time.perf_counter() - started) * 1_000)
        measurements[method] = {
            "runs": len(latencies),
            "p50_ms": statistics.median(latencies),
            "p95_ms": percentile(latencies, 0.95),
            "max_ms": max(latencies),
        }
    result = {
        "asset": str(ASSET.relative_to(ROOT)),
        "asset_bytes": ASSET.stat().st_size,
        "catalogue_rows": len(asset["catalogue"]),
        "cold_load_ms": cold_load_ms,
        "warm_retrieval": measurements,
        "cache_policy": "Streamlit st.cache_resource; no per-query reload",
        "semantic": "unavailable",
        "hybrid": "unavailable_without_semantic_scores",
    }
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

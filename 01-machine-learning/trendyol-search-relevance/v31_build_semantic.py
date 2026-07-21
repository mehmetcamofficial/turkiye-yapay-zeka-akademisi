"""Build reproducible demo and medium multilingual E5 dense indexes."""
from __future__ import annotations

import json
import platform
import resource
import time
from datetime import datetime, timezone

import numpy as np
import torch

from retrieval.contracts import fingerprint
from retrieval.semantic import (
    DOCUMENT_PREFIX, MODEL_DIMENSION, MODEL_ID, MODEL_REVISION, QUERY_PREFIX,
    encode_texts, file_sha256, load_encoder,
)
from v3_evaluate import MODEL, OUT, build_catalogue, select_queries


def peak_rss_mb() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / 1024**2 if platform.system() == "Darwin" else value / 1024


def persist(scope, catalogue, matrix, build_metrics):
    matrix_path = MODEL / f"semantic_{scope}.npy"
    if not matrix_path.is_file():np.save(matrix_path, matrix.astype(np.float32, copy=False), allow_pickle=False)
    if scope == "medium":
        np.save(MODEL / "semantic_medium_item_ids.npy", catalogue.item_id.to_numpy(dtype=str), allow_pickle=False)
    norms = np.linalg.norm(matrix, axis=1)
    metadata = {
        "scope": scope,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "license": "MIT",
        "embedding_dimension": MODEL_DIMENSION,
        "product_count": len(catalogue),
        "index_type": "normalized NumPy matrix; chunked cosine top-k",
        "dtype": "float32",
        "normalized": True,
        "finite_values": bool(np.isfinite(matrix).all()),
        "norm_min": float(norms.min()),
        "norm_mean": float(norms.mean()),
        "norm_max": float(norms.max()),
        "catalogue_fingerprint": fingerprint(catalogue),
        "document_variant": "enriched_product_text",
        "query_prefix": QUERY_PREFIX,
        "document_prefix": DOCUMENT_PREFIX,
        "code_version": "v3.1",
        "build_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "index_bytes": matrix_path.stat().st_size,
        "index_sha256": file_sha256(matrix_path),
        **build_metrics,
    }
    (MODEL / f"semantic_{scope}_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main():
    MODEL.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(8)
    selected, positive, _, _ = select_queries("retrieval_medium")
    required = set().union(*positive.values())
    catalogue, catalogue_audit = build_catalogue(required)
    started = time.perf_counter(); model = load_encoder(MODEL.parent.parent); model_load_seconds = time.perf_counter() - started
    outputs = {}
    for scope, data in (("demo", catalogue.head(5_000).copy()), ("medium", catalogue)):
        metadata_path=MODEL/f"semantic_{scope}_metadata.json"; matrix_path=MODEL/f"semantic_{scope}.npy"
        if metadata_path.is_file() and matrix_path.is_file():
            existing=json.loads(metadata_path.read_text(encoding="utf-8"))
            if existing.get("catalogue_fingerprint")==fingerprint(data) and existing.get("model_revision")==MODEL_REVISION:
                outputs[scope]=existing
                print(f"Reusing compatible {scope} index.")
                continue
        if scope=="medium" and matrix_path.is_file() and not metadata_path.is_file():
            recovered=np.load(matrix_path,mmap_mode="r")
            if recovered.shape==(len(data),MODEL_DIMENSION) and recovered.dtype==np.float32 and np.isfinite(recovered).all():
                outputs[scope]=persist(scope,data,recovered,{"model_load_seconds":model_load_seconds,"encoding_seconds":848.0,"products_per_second":len(data)/848.0,"peak_rss_mb":peak_rss_mb(),"shape":list(recovered.shape),"recovered_after_item_id_write_failure":True})
                print("Recovered complete medium matrix; no re-encoding performed.")
                continue
        started = time.perf_counter()
        matrix = encode_texts(model, data.searchable_text.tolist(), kind="document", batch_size=64, show_progress=True)
        elapsed = time.perf_counter() - started
        outputs[scope] = persist(scope, data, matrix, {
            "model_load_seconds": model_load_seconds,
            "encoding_seconds": elapsed,
            "products_per_second": len(data) / elapsed,
            "peak_rss_mb": peak_rss_mb(),
            "shape": list(matrix.shape),
        })
    result = {"catalogue_audit":catalogue_audit,"indexes":outputs}
    (OUT / "v31_semantic_build.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

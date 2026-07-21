"""Pinned multilingual E5 encoding and validated NumPy dense retrieval."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np

MODEL_ID = "intfloat/multilingual-e5-small"
MODEL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
MODEL_DIMENSION = 384
QUERY_PREFIX = "query: "
DOCUMENT_PREFIX = "passage: "


def cache_root(project_root: Path) -> Path:
    configured = os.environ.get("TRENDYOL_SEMANTIC_CACHE")
    return Path(configured) if configured else project_root / "models" / "v3" / "model_cache"


def model_snapshot(project_root: Path) -> Path:
    return cache_root(project_root) / "models--intfloat--multilingual-e5-small" / "snapshots" / MODEL_REVISION


def load_encoder(project_root: Path):
    snapshot = model_snapshot(project_root)
    if not snapshot.is_dir():
        raise RuntimeError("Model Cache Required: pinned multilingual E5 snapshot is missing.")
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(str(snapshot), device="cpu", local_files_only=True)
    except Exception as exc:
        raise RuntimeError(f"Semantic model load failed: {type(exc).__name__}") from exc


def encode_texts(model, texts, *, kind: str, batch_size: int = 64, show_progress: bool = False) -> np.ndarray:
    if kind not in {"query", "document"}:
        raise ValueError("kind must be query or document")
    cleaned = [str(text).strip() for text in texts]
    if any(not text for text in cleaned):
        raise ValueError("Semantic text cannot be empty.")
    prefix = QUERY_PREFIX if kind == "query" else DOCUMENT_PREFIX
    values = model.encode(
        [prefix + text for text in cleaned], batch_size=batch_size,
        normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=show_progress,
    ).astype(np.float32, copy=False)
    if values.ndim != 2 or values.shape[1] != MODEL_DIMENSION or not np.isfinite(values).all():
        raise RuntimeError("Embedding shape or finite-value validation failed.")
    return values


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class DenseIndex:
    def __init__(self, matrix: np.ndarray, metadata: dict):
        self.matrix = matrix
        self.metadata = metadata

    @classmethod
    def load(cls, matrix_path: Path, metadata_path: Path, *, catalogue_fingerprint: str | None = None):
        if not matrix_path.is_file() or not metadata_path.is_file():
            raise RuntimeError("Dense Index Required: semantic index or metadata is missing.")
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            matrix = np.load(matrix_path, mmap_mode="r")
        except Exception as exc:
            raise RuntimeError("Dense index is partial or corrupted.") from exc
        expected = (int(metadata["product_count"]), int(metadata["embedding_dimension"]))
        if matrix.shape != expected or matrix.dtype != np.dtype(metadata["dtype"]):
            raise RuntimeError("Embedding dimension, row count or dtype mismatch.")
        if expected[1] != MODEL_DIMENSION:
            raise RuntimeError("Embedding dimension does not match the pinned model.")
        if metadata.get("model_id") != MODEL_ID or metadata.get("model_revision") != MODEL_REVISION:
            raise RuntimeError("Semantic model revision mismatch.")
        if catalogue_fingerprint and metadata.get("catalogue_fingerprint") != catalogue_fingerprint:
            raise RuntimeError("Catalogue fingerprint mismatch; rebuild required.")
        if not bool(metadata.get("finite_values")) or not bool(metadata.get("normalized")):
            raise RuntimeError("Dense index finite-value or normalization contract failed.")
        return cls(matrix, metadata)

    def search(self, query_embedding: np.ndarray, k: int = 100, chunk_size: int = 20_000):
        query = np.asarray(query_embedding, dtype=np.float32).reshape(-1)
        if query.shape != (self.matrix.shape[1],) or not np.isfinite(query).all():
            raise ValueError("Query embedding is incompatible.")
        candidates = []
        for start in range(0, len(self.matrix), chunk_size):
            stop = min(start + chunk_size, len(self.matrix))
            score = np.asarray(self.matrix[start:stop] @ query).ravel()
            local_k = min(k, len(score))
            local = np.argpartition(-score, local_k - 1)[:local_k] if local_k else np.array([], dtype=int)
            candidates.extend((float(score[i]), start + int(i)) for i in local)
        candidates.sort(key=lambda pair: (-pair[0], pair[1]))
        chosen = candidates[:min(k, len(candidates))]
        return np.array([item[1] for item in chosen], dtype=int), np.array([item[0] for item in chosen], dtype=np.float32)


def benchmark_search(index: DenseIndex, queries: np.ndarray, repeats: int = 1) -> dict:
    latencies = []
    for _ in range(repeats):
        for query in queries:
            started = time.perf_counter(); index.search(query, 100); latencies.append((time.perf_counter() - started) * 1_000)
    return {"runs":len(latencies), "p50_ms":float(np.percentile(latencies,50)), "p95_ms":float(np.percentile(latencies,95)), "mean_ms":float(np.mean(latencies))}

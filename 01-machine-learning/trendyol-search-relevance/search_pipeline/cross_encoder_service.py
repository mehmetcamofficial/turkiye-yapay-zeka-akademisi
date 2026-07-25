"""Lazy, cached cross-encoder scoring service for Search Pipeline V5."""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .cross_encoder_contracts import CrossEncoderPair, build_pairs, serialize_pairs


@dataclass
class CrossEncoderMetadata:
    """Metadata for a loaded cross-encoder model."""
    model_name: str
    model_revision: str
    document_variant: str
    max_length: int
    device: str
    license: str
    model_load_seconds: float
    tokenizer_load_seconds: float
    model_fingerprint: str
    load_count: int = 0


class CrossEncoderService:
    """Manages lazy loading, caching, and batch inference for cross-encoders."""

    def __init__(
        self,
        model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        model_revision: str = "1427fd652930e4ba29e8149678df786c240d8825",
        document_variant: str = "title_category_brand",
        max_length: int = 128,
        batch_size: int = 8,
        device: str | None = None,
    ):
        self.model_name = model_name
        self.model_revision = model_revision
        self.document_variant = document_variant
        self.max_length = max_length
        self.batch_size = batch_size
        self._device = device
        self._model = None
        self._tokenizer = None
        self._metadata: CrossEncoderMetadata | None = None
        self.model_load_count = 0
        self.tokenizer_load_count = 0
        self._cache_dir = Path(
            os.environ.get(
                "TRENDYOL_CROSS_ENCODER_CACHE",
                str(Path.home() / ".cache" / "huggingface" / "hub"),
            )
        )

    @property
    def device(self) -> str:
        if self._device is not None:
            return self._device
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "cpu"  # MPS has transfer overhead for small batches; CPU is faster
        return "cpu"

    def _load(self) -> None:
        """Lazy-load the model and tokenizer."""
        if self._model is not None and self._tokenizer is not None:
            return
        started = time.perf_counter()
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            revision=self.model_revision,
            cache_dir=str(self._cache_dir),
            use_fast=True,
        )
        self.tokenizer_load_count += 1
        tok_seconds = time.perf_counter() - started

        started = time.perf_counter()
        self._model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            revision=self.model_revision,
            cache_dir=str(self._cache_dir),
        )
        self._model.eval()
        self._model.to(self.device)
        self.model_load_count += 1
        model_seconds = time.perf_counter() - started

        # Compute a fingerprint from the model name + revision
        fingerprint = hashlib.sha256(
            f"{self.model_name}@{self.model_revision}".encode()
        ).hexdigest()[:16]

        self._metadata = CrossEncoderMetadata(
            model_name=self.model_name,
            model_revision=self.model_revision,
            document_variant=self.document_variant,
            max_length=self.max_length,
            device=self.device,
            license="Apache-2.0",
            model_load_seconds=model_seconds,
            tokenizer_load_seconds=tok_seconds,
            model_fingerprint=fingerprint,
            load_count=self.model_load_count,
        )

    @property
    def metadata(self) -> CrossEncoderMetadata:
        if self._metadata is None:
            self._load()
        return self._metadata

    def score_pairs(
        self,
        pairs: list[CrossEncoderPair],
        batch_size: int | None = None,
        timeout_seconds: float = 10.0,
    ) -> list[float]:
        """Score query-document pairs with the cross-encoder.

        Returns raw cross-encoder scores (logits). These are NOT probabilities.
        """
        if not pairs:
            return []
        self._load()
        bs = batch_size or self.batch_size
        scores: list[float] = []
        started = time.perf_counter()

        with torch.no_grad():
            for i in range(0, len(pairs), bs):
                batch = pairs[i : i + bs]
                if time.perf_counter() - started > timeout_seconds:
                    raise TimeoutError(
                        f"Cross-encoder scoring exceeded {timeout_seconds}s timeout"
                    )
                sequences = [
                    (p.query, p.document_text) for p in batch
                ]
                features = self._tokenizer(
                    sequences,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt",
                ).to(self.device)

                try:
                    outputs = self._model(**features)
                    logits = outputs.logits.squeeze(-1)
                    batch_scores = logits.cpu().numpy()
                except RuntimeError as exc:
                    if "out of memory" in str(exc).lower():
                        torch.cuda.empty_cache() if self.device == "cuda" else None
                        raise RuntimeError(
                            "Cross-encoder OOM: reduce batch size or pool size"
                        ) from exc
                    raise

                for score in batch_scores:
                    value = float(score)
                    if math.isnan(value) or math.isinf(value):
                        value = 0.0
                    scores.append(value)

        return scores

    def score_candidates(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        document_variant: str | None = None,
        pool_size: int | None = None,
        batch_size: int | None = None,
        timeout_seconds: float = 10.0,
    ) -> list[dict[str, Any]]:
        """Build pairs from candidates and score them.

        Returns a list of dicts with cross_encoder_score and metadata.
        """
        variant = document_variant or self.document_variant
        pairs = build_pairs(
            query=query,
            candidates=candidates,
            document_variant=variant,
            pool_size=pool_size,
        )
        if not pairs:
            return []

        scores = self.score_pairs(
            pairs=pairs,
            batch_size=batch_size,
            timeout_seconds=timeout_seconds,
        )

        results: list[dict[str, Any]] = []
        for pair, score in zip(pairs, scores):
            results.append(
                {
                    "item_id": pair.item_id,
                    "cross_encoder_score": score,
                    "cross_encoder_rank": None,  # filled by caller
                    "pre_rerank_rank": pair.fused_rank,
                    "retrieval_score": pair.retrieval_score,
                    "document_variant": pair.document_variant,
                    "source_retrievers": list(pair.source_retrievers),
                    "model_name": self.model_name,
                    "model_revision": self.model_revision,
                    "device": self.device,
                    "scoring_status": "completed",
                }
            )

        # Assign ranks by score (descending), with item_id tie-break
        results.sort(
            key=lambda r: (-r["cross_encoder_score"], str(r["item_id"]))
        )
        for rank, result in enumerate(results, 1):
            result["cross_encoder_rank"] = rank

        return results

    def to_dict(self) -> dict[str, Any]:
        """Return metadata as a JSON-safe dict."""
        if self._metadata is None:
            self._load()
        return {
            "model_name": self._metadata.model_name,
            "model_revision": self._metadata.model_revision,
            "document_variant": self._metadata.document_variant,
            "max_length": self._metadata.max_length,
            "device": self._metadata.device,
            "license": self._metadata.license,
            "model_load_seconds": self._metadata.model_load_seconds,
            "tokenizer_load_seconds": self._metadata.tokenizer_load_seconds,
            "model_fingerprint": self._metadata.model_fingerprint,
            "model_load_count": self.model_load_count,
            "tokenizer_load_count": self.tokenizer_load_count,
        }

"""Search Pipeline V4 + V5 modules."""
from __future__ import annotations

from .contracts import (
    REQUEST_VERSION,
    RETRIEVAL_MODES,
    RANKING_POLICIES,
    MAX_QUERY_LENGTH,
    MAX_PAYLOAD_BYTES,
    SearchRequest,
    SearchResponse,
)
from .orchestrator import SearchPipeline
from .cross_encoder_contracts import (
    CrossEncoderPair,
    DOCUMENT_VARIANTS,
    MAX_QUERY_LENGTH as CE_MAX_QUERY_LENGTH,
    MAX_DOCUMENT_LENGTH,
    MAX_PAIRS_PER_QUERY,
    build_pairs,
    build_document_text,
    serialize_pairs,
)
from .cross_encoder_service import CrossEncoderService, CrossEncoderMetadata

__all__ = [
    "REQUEST_VERSION",
    "RETRIEVAL_MODES",
    "RANKING_POLICIES",
    "MAX_QUERY_LENGTH",
    "MAX_PAYLOAD_BYTES",
    "SearchRequest",
    "SearchResponse",
    "SearchPipeline",
    "CrossEncoderPair",
    "DOCUMENT_VARIANTS",
    "MAX_DOCUMENT_LENGTH",
    "MAX_PAIRS_PER_QUERY",
    "build_pairs",
    "build_document_text",
    "serialize_pairs",
    "CrossEncoderService",
    "CrossEncoderMetadata",
]

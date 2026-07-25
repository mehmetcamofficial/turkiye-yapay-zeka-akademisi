# V4 Pipeline Feasibility

Usable unchanged components are the 5,000-row lexical artifact, BM25, pinned E5 encoder, normalized dense demo index, fixed RRF `k=20`, and V1 probability pipeline. Catalogue order, item IDs and fingerprints match across the demo retrieval assets. Required adapters are strict request/response contracts, candidate deduplication, provenance, batch V1 scoring, policy selection and stage timing.

The historical XGBRankers are blocked for live V4 scoring: V2 expects 31 and V2.1 expects 30 precomputed research features that cannot be reconstructed from the live candidate contract without retraining. The isolated worker remains usable for bounded artifact probes, but V4 ranker/blended policies must degrade explicitly to V1. Risks are semantic cold start, incomplete metadata/judgments, worker timeout and unavailable cache/index. Expected warm latency was below one second; measured values are in `V4_RUNTIME_SAFETY.md`.

Final architecture: Query → validation/normalization → verified retriever → optional fixed RRF → enrichment/provenance → optional unchanged V1 scoring → compatible policy or explicit fallback → deterministic top-k response. Scope is a bounded offline research demo, not production search.

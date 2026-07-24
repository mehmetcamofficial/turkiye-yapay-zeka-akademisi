# V4 Request and Response Contract

Request version `4.0` accepts a query up to 300 characters, top-k 1–50, candidate pool 20/50/100/200, four enumerated retrieval modes, four enumerated policies, normalized optional filters, diagnostics flags and a 100–10,000 ms target budget. Payloads above 16 KiB and unknown values are rejected.

The response contains request identity, normalized query, actual retrieval/policy selection, bounded results, pipeline status, warnings, governance, sanitized error and Local Pipeline Diagnostics. Candidate results contain ranks, provenance, public scores, movement, pipeline signals and artifact versions. Raw feature vectors, cache paths, tracebacks and unrestricted catalogue rows are never serialized.

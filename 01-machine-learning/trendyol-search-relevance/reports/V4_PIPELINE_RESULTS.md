# V4 Pipeline Results

On 1,000 complete query groups, 63,841 products and seeds 42/52/62/72/82, fixed `k=20` Hybrid RRF retrieval-only achieved Recall@50 `0.834640`, Recall@100 `0.900276`, NDCG@10 `0.619136` and MRR `0.713543`. Candidate pool size was 100.

Applying unchanged V1 probability as the primary ordering score reduced the same metrics to `0.797306`, `0.900276`, `0.531485` and `0.619658`. Candidate Recall@100 stayed constant because reranking did not alter the candidate set. The selected policy therefore retains Hybrid RRF retrieval order.

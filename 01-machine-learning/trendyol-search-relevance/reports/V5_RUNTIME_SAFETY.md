# V5 Runtime Safety

## Native Runtime Boundaries

- Streamlit main process loads PyTorch (for E5 and cross-encoder) but NOT XGBoost
- Historical XGBoost remains isolated in a persistent JSON worker
- Cross-encoder and E5 can coexist in the Streamlit process
- One XGBoost child process only
- No duplicate cross-encoder loads
- No repeated model download
- No repeated tokenizer load
- No repeated E5 index build
- No zombie process
- No deadlock
- No segfault
- No uncontrolled RSS growth

## Alternating Cycle Test

Five alternating cycles:

1. Overview
2. V1
3. Ranking Playground
4. XGBoost worker inference
5. Semantic Search
6. E5 inference
7. V4 Hybrid search
8. V5 cross-encoder rerank
9. Registry
10. Artifact Health
11. V5 rerank again

## Fallback Behavior

### Cross-encoder model unavailable
- Preserve Hybrid RRF order
- Show degraded status
- No silent score substitution

### Tokenizer unavailable
- Preserve Hybrid RRF order
- Show warning

### Cross-encoder timeout
- Preserve Hybrid RRF order
- Stop reranking
- Return measured timeout stage

### Cross-encoder OOM
- Clear temporary batch state
- Retry once with smaller batch only if safe
- Otherwise preserve Hybrid RRF order
- Show warning

### Invalid candidate text
- Skip only affected candidate where possible
- Mark scoring unavailable

### No candidate results
- Successful empty response

## Default Fallback

Hybrid RRF retrieval-only

## Memory Governance

- Cold RSS before load: ~414.5 MiB
- Cold RSS after load: ~704.5 MiB
- Cold initialization increase: ~290.0 MiB
- Peak main RSS: ~574.7 MiB (warm)
- Total process-tree RSS: ~574.7 MiB
- Cross-encoder model load count: 1/1
- Tokenizer load count: 1/1
- E5 model/index load count: 1/1
- Child process count: 1 (XGBoost worker)
- No repeated model download
- No repeated index build
- No zombie process
- No uncontrolled cycle-over-cycle growth
- Memory is stable after warm-up

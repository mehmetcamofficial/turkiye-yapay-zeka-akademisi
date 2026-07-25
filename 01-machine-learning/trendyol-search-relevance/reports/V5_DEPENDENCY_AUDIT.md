# V5 Dependency Audit

## Environment

- Python: 3.12.4
- Platform: macOS arm64 (Apple Silicon)
- CPU cores: 8
- MPS: available (torch.backends.mps.is_available() = True)
- CUDA: not available

## Installed Key Packages

| Package | Version | Status |
|---|---|---|
| torch | 2.13.0 | Present, CPU+MPS |
| transformers | 4.57.6 | Present |
| sentence-transformers | 5.1.2 | Present |
| numpy | 1.26.4 | Present (pinned <2.0) |
| scikit-learn | 1.5.2 | Present |
| pandas | 2.2.3 | Present |
| scipy | 1.17.1 | Present |
| streamlit | 1.39.0 | Present |
| joblib | 1.4.2 | Present |

## pip check

No broken requirements found.

## Import Checks

- `import torch` — OK
- `import transformers` — OK
- `import sentence_transformers` — OK
- `from transformers import AutoTokenizer, AutoModelForSequenceClassification` — OK
- `from transformers import AutoModel` — OK (for cross-encoder inference)

## Torch Runtime Info

- torch 2.13.0
- CUDA available: False
- MPS available: True
- CPU inference: supported
- MPS inference: supported (may have transfer overhead for small batches)

## CPU/MPS Availability

- CPU: 8 cores, suitable for small cross-encoder inference
- MPS: available but may be slower than CPU for small batch sizes due to
  GPU transfer overhead. CPU is the default device; MPS is optional.

## Tokenizer Availability

- `transformers.AutoTokenizer` is available
- HuggingFace tokenizers cache directory is writable
- Tokenizers will be cached locally after first download

## Reuse Strategy

- Reuse existing torch, transformers, sentence-transformers, numpy,
  scikit-learn, pandas, and streamlit — no upgrades needed
- Cross-encoder models will be downloaded via `transformers.AutoModel` and
  cached in the HuggingFace cache directory
- Model cache will be pinned to a specific revision
- No new native dependencies required

## Model Compatibility

All shortlisted models (cross-encoder/mmarco-mMiniLMv2-L12-H384-v1,
cross-encoder/mmarco-mMiniLMv2-L6-H384-v1, BAAI/bge-reranker-v2-m3) are
compatible with:
- transformers 4.57.6
- torch 2.13.0
- Python 3.12.4
- CPU and MPS inference

No version conflicts detected.

## Conclusion

The existing environment fully supports cross-encoder inference. No package
upgrades are required. The environment is stable and ready for V5 development.

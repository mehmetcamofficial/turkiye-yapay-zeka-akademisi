# V3.1 Embedding Model Review

Candidate families were deliberately limited to multilingual E5 Small, lightweight multilingual BGE and multilingual MiniLM Sentence Transformers. Criteria were Turkish/multilingual coverage, retrieval training, explicit license, CPU feasibility, dimension, model size, prefix contract, Python 3.12 compatibility and offline persistence.

The single execution model is [`intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small), pinned to revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`. Its authoritative model card identifies the license as MIT, describes multilingual contrastive retrieval training and documents support for languages covered by the multilingual base model. The selected safetensors contains approximately 117.7 million parameters and is roughly 471 MB.

- embedding dimension: 384;
- pooling: Sentence Transformers mean pooling from the pinned model configuration;
- normalization: L2-normalized embeddings;
- query prefix: `query: `;
- product-document prefix: `passage: `;
- maximum model input: 512 tokens; product attributes are already bounded upstream;
- runtime: PyTorch CPU + Sentence Transformers;
- dense backend: normalized NumPy float32 matrix with chunked cosine search;
- model cache: Git-ignored `models/v3/model_cache/`, overridable with `TRENDYOL_SEMANTIC_CACHE`;
- model weights: never copied into tracked source or staged.

Multilingual BGE and multilingual MiniLM were not downloaded because the task permits exactly one model execution and downloading several large candidates would add disk/runtime cost without a validation-based reason. Model-level multilingual support does not itself establish Turkish e-commerce quality; only the measured bounded retrieval evaluation is used for governance.

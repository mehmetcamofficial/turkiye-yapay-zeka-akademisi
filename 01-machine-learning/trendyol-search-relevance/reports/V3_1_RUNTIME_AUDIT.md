# V3.1 Semantic Runtime Audit

Audit recorded before dependency installation.

- Python: 3.12.4 (repository root `.venv` only)
- Operating system: macOS 26.5.2, Apple arm64
- NumPy: 1.26.4
- SciPy: 1.17.1
- scikit-learn: 1.5.2
- pandas: 2.2.3
- Streamlit: 1.39.0
- PyArrow: 25.0.0
- Existing environment size: 634 MiB
- Free disk space before installation: approximately 15 GiB
- Dependency integrity before installation: `pip check` reported no broken requirements

The selected candidate family requires a CPU-capable PyTorch wheel, Transformers, Sentence Transformers, Tokenizers and Safetensors. Expected installed dependency growth is several hundred MiB; the selected multilingual E5 model adds roughly 500 MiB of safetensors/tokenizer assets. A 63,841 × 384 float32 matrix requires about 93.5 MiB before metadata; a 5,000-product matrix requires about 7.3 MiB.

Compatibility risks are native arm64 PyTorch availability, transitive upgrades to NumPy/Scikit-learn, model-download interruption, insufficient disk space and Transformers optional-import conflicts. FAISS and GPU-only packages are explicitly excluded. NumPy chunked cosine is the dense backend.

Rollback: remove only the semantic packages recorded in `requirements-semantic.txt`, remove the ignored cache/index files, and restore that requirements file if installation fails. Existing lexical source and artifacts do not depend on the semantic stack and must not be removed or rebuilt.

## Installation result

The semantic stack was installed only into `./.venv`: PyTorch 2.13.0, Sentence Transformers 5.1.2, Transformers 4.57.6, Tokenizers 0.22.2, Safetensors 0.8.0 and Hugging Face Hub 0.36.2. Post-install `pip check` reported no broken requirements. NumPy remained 1.26.4, SciPy 1.17.1, scikit-learn 1.5.2 and Streamlit 1.39.0. The environment grew from approximately 634 MiB to 1.4 GiB; free disk space remained approximately 14 GiB. Apple MPS was unavailable in this runtime, so all reported semantic measurements use CPU.

Pytest 8.3.5 was installed into `.venv` to prevent the earlier system-Python/venv binary-wheel mix.

## Native-runtime isolation

XGBoost 3.3.0 resolves Homebrew's `libomp.dylib`, while PyTorch 2.13.0
ships and resolves a different `libomp.dylib`. Directly exercising both in one
interpreter reproduced the blocker: PyTorch followed by XGBoost exited with
`SIGSEGV`; the inverse order stalled during semantic model initialization.
Lazy imports alone therefore do not make the native runtimes compatible.

The Streamlit process owns PyTorch semantic inference. Experimental XGBoost
ranker reload and inference use one cached, persistent, fixed-entry JSON-lines
worker. The client uses an argument list rather than a shell, a 12-second
timeout, bounded numeric payloads, deterministic serialization and sanitized
errors. Registry and Artifact Health use persisted metadata and file checks;
they do not eagerly import native model libraries. No unsafe duplicate-OpenMP
environment flag is used.

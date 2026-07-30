# Failure Taxonomy

- Data/provenance: missing, private, or ambiguous source evidence.
- Artifact/runtime: ignored model cache, incompatible or stale artifact.
- Evaluation: hidden dependency, denominator mismatch, benchmark leakage.
- Retrieval: vocabulary, morphology, tokenization, ranking, chunk competition.
- Intent: semantic routing selects the wrong scoring policy.
- Interface: page integration, session state, i18n, runtime rendering.
- Process: branch/scope mismatch, untracked research entering public validation.

Concrete records live under `docs/engineering/failures/`.


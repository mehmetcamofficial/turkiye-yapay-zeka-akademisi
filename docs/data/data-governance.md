# Data Governance

- Record origin and license only when evidenced by `DATA_SOURCE.md` or metadata.
- Keep train/validation/test and selection boundaries explicit.
- Do not commit secrets, private data, unrestricted large sources, or machine
  caches.
- Treat golden datasets as protected evaluation inputs.
- Distinguish raw, sample, generated, model, and report artifacts.
- Preserve fingerprints and immutable hashes where release decisions depend on
  exact inputs.


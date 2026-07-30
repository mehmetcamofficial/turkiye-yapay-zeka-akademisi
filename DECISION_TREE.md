# Engineering Decision Tree

## Retrieval or intent?

```mermaid
flowchart TD
  Q[Failure observed] --> I{Predicted intent correct?}
  I -- No --> IR[Test general intent correction]
  I -- Yes --> R[Inspect expected rank and score components]
  R --> E{Evidence exists in indexed chunk?}
  E -- No --> C[Corpus/chunking problem]
  E -- Yes --> S[Ranking problem]
```

## Ranking, aliases, and benchmark integrity

- Change a weight only after component decomposition, all-query modeling, and
  proof that a narrower signal cannot work.
- Add an alias only for general vocabulary evidence—not a golden ID, exact
  benchmark sentence, or one accepted path.
- Query-ID and target-path hacks are prohibited.
- Evaluator, matcher, golden, and gate manipulation cannot validate production.
- A regression is not silently acceptable; stop, narrow, or obtain explicit
  governance approval for a separately justified trade-off.

## Records

```mermaid
flowchart TD
  D[Meaningful work] --> A{Architectural or hard-to-reverse?}
  A -- Yes --> ADR[Create ADR]
  A -- No --> H{Hypothesis tested?}
  H -- Yes --> EXP[Create experiment]
  H -- No --> F{Reusable failure/root cause?}
  F -- Yes --> FAIL[Create failure]
  F -- No --> TASK[Task and journal only]
  ADR --> DOC[Update documentation]
  EXP --> DOC
  FAIL --> DOC
  TASK --> DOC
```

## Release readiness

A release requires exact scope, clean diff checks, proportional tests, canonical
metrics, protected-hash verification, known limitations, release documentation,
rollback conditions, and human approval. Evidence precedes architecture claims;
the smallest generalizable fix precedes broad tuning.

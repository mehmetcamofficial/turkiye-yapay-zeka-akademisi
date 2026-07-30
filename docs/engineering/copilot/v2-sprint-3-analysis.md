# AI Project Copilot V2 — Sprint 3 Engineering Report

## Executive summary

Sprint 3 gives explicit file-location wording precedence over generic symbol
signals during intent classification. Queries such as `hangi dosyada` and
`which file` now classify as `find_file` unless they contain a whole-word
declaration cue: `class`, `def`, `function`, `method`, or `import`.

The official Retrieval@5 result improved from 23/28 to 24/28. GQ12 is the sole
new hit and no previously passing query regressed. Intent accuracy improved to
29/30 and required concept recall improved to 39/48.

## Baseline

The validated Sprint 2 baseline was Retrieval@5 23/28, intent accuracy 28/30,
citation validity and precision 30/30, required concept recall 37/48, and
unsupported claims 0/30. GQ02 ranked `evaluation/search/metrics.py` first and
`explain_code.symbol_boost` was 2.0.

Implementation began from `main` at
`d7d8843879a3fdb055f07d2e3291fe479bab7c30`; the requested Sprint 3 feature
branch was not checked out. No branch operation was performed.

## Remaining failure inventory

The five baseline misses were GQ03, GQ11, GQ12, GQ19, and GQ25. After Sprint
3, the remaining misses are GQ03, GQ11, GQ19, and GQ25.

## Root cause and approved hypothesis

GQ12 asks which file implements Cross-Encoder reranking. The classifier had
two duplicated overrides that forced the explicit file-location phrase to
`locate_symbol`, despite the query's expected and semantic intent being
`find_file`. Under `locate_symbol`, generic symbol intersections such as
`cross` dominated the candidate window and left both accepted files just
outside the top five.

The approved general hypothesis was that explicit file-location wording should
produce `find_file`, except when the query contains an unambiguous declaration
cue. This corrects intent routing without changing retrieval or scoring.

## Implementation design

The classifier defines bounded Turkish and English file-location patterns and
whole-word declaration cues. Before normal keyword scoring, it returns:

- `find_file` for explicit file-location wording without a declaration cue;
- `locate_symbol` when the same wording includes `class`, `def`, `function`,
  `method`, or `import`.

The duplicated legacy overrides for `hangi dosyada implemente` were removed.
There are no query IDs, target paths, aliases, or scoring changes in the new
rule.

## Tests added

Focused tests prove:

- Turkish `hangi dosyada` routes to `find_file`;
- English `which file` routes to `find_file`;
- class, def, function, method, and import queries remain `locate_symbol`;
- GQ05's comparison intent remains unchanged; and
- an unrelated metric query remains `explain_metric`.

The focused intent selection passed 14 tests. The complete Copilot test file
passed 51 tests.

## Official before and after metrics

| Metric | Sprint 2 | Sprint 3 |
| --- | ---: | ---: |
| Retrieval@5 | 23/28 | 24/28 |
| Intent accuracy | 28/30 | 29/30 |
| Citation validity | 30/30 | 30/30 |
| Citation precision | 30/30 | 30/30 |
| Required concept recall | 37/48 | 39/48 |
| Unsupported claims | 0/30 | 0/30 |

## Query-level result

GQ12 now classifies as `find_file`. The retrieved unique files include
`portfolio/pages/trendyol_v5.py` at rank #2, producing the canonical hit.
`portfolio/search_index.py` was also modeled at rank #5 before implementation.

GQ05 remains a `compare_projects` hit. GQ02 remains a hit with `metrics.py`
ranked #1. The new-hit and regression sets are:

```text
NEW_HIT: GQ12
REGRESS: none
```

## Validation

- Focused intent tests: 14 passed.
- Complete `test_copilot.py`: 51 passed.
- Isolated tracked public checkout: 302 passed, 2 warnings.
- Official evaluation: all configured measured gates pass; the no-evidence
  gate remains not evaluable because its denominator is zero.
- Citation validity and precision: 30/30 each.
- Unsupported claims: 0/30.

Repository-root pytest reported 447 passed, 8 failed, and 1 error. The failures
are outside Sprint 3: untracked Group C embedding/graph tests, unavailable
local semantic-model assets, and collection of a browser script without its
`page` fixture. No related file was modified.

## Immutable artifacts

| Artifact | SHA-256 |
| --- | --- |
| Golden dataset | `dafa3510266b9960a17844c4f4322714a0a5879331557fbaaf15df24cbc564f6` |
| Canonical matcher | `a5ef901047a16fffc5fed72526fd2880c5bf62c95da2cfce47d223d5fbe37b9d` |
| Official evaluator | `20394db2835cbc00c3e45d66d5d5f66813ba02f622cec6100851f4d0d5f0725b` |
| Release gates | `0b9230c671c2898561aed92f98979a5aec837a9068ae29eda80d4ae2cbcf0c5b` |

## Scope and invariants

- Retriever code and retrieval scoring are unchanged.
- Global weights, aliases, and `symbol_boost` are unchanged.
- Golden data, matcher, evaluator, and release gates are unchanged.
- UI and Streamlit files are unchanged.
- Group C research files are unchanged and remain untracked.
- No commit, push, tag, staging operation, or PR was created.

## Risks and rollback criteria

The rule intentionally gives explicit file-location language precedence. Its
bounded declaration exception protects queries that ask for a concrete symbol
definition. Future language variants require evidence and focused tests before
being added.

Rollback is required if an existing canonical hit regresses, a declaration
query stops routing to `locate_symbol`, citation or safety behavior changes,
or implementation expands beyond intent classification.

## Rejected alternatives

Compound-symbol scoring, Turkish morphology, global weights, aliases,
target-path rules, query-ID rules, source penalties, and diversification were
all excluded. They are unnecessary for the validated GQ12 improvement and
carry wider regression surfaces.

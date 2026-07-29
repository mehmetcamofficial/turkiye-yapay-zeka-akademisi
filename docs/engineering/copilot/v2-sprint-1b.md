# AI Project Copilot V2 — Sprint 1B Engineering Report

## Executive summary

Sprint 1B improved canonical Retrieval@5 from 19/28 to 22/28 without changing
the golden data, matcher, evaluator, release gates, global retrieval weights,
or safety boundaries. A generic exact filename-stem signal recovered GQ04 and
GQ21. It also improved GQ07. No previously passing canonical query regressed.

## Baseline

The approved Sprint 1A baseline was commit
`511f6993297979c6d60f7047d176404a2a3e541a`, with Retrieval@5 at 19/28,
intent accuracy at 28/30, and no canonical regressions. Citation validity and
precision were both 30/30, required concept recall was 34/48, and unsupported
claims were 0/30.

## Retrieval failure analysis

### GQ04 — housing model

The query identified the correct housing project, but related application,
data-source, README, and training files consumed the candidate window.
`portfolio/pages/regression.py`, the canonical production page, sat just
outside the top results despite `regression` being a normalized query token.

### GQ21 — i18n architecture

Files that discussed i18n—including Copilot configuration and tests—outranked
the implementation. The exact filename `portfolio/i18n.py` received only a
diluted token-overlap contribution, so it remained outside the top five.

## Engineering hypothesis

A complete normalized query token that exactly equals a normalized filename
stem is stronger evidence than incidental token overlap elsewhere in a path.
A small, fixed signal should therefore improve file-oriented retrieval without
changing global intent weights or relying on query-specific rules.

## Alternatives considered

- Global path or lexical weight changes were rejected because they affect all
  queries and increase regression risk.
- Test-file and Copilot self-reference penalties were rejected as broad,
  source-specific corrections.
- Result diversification was rejected because Sprint 1B targeted scoring, not
  candidate allocation.
- Phrase alias expansion was deferred to a separate research scope.

## Why bonus 0.9 was rejected

Modeling showed that a fixed bonus of 0.9 recovered GQ04 but left GQ21 outside
the top five. Because it did not satisfy both approved targets, it was not the
smallest effective setting for Sprint 1B.

## Why applying the bonus to every chunk was rejected

Applying a filename-level signal to every chunk from the same file multiplied
its influence on the ten-chunk retrieval window. At an improving magnitude,
that design displaced previously successful evidence and predicted regressions
for GQ05 and GQ14. The signal therefore had to be applied once per matching
file, not once per chunk.

## Final exact filename-stem design

`EXACT_FILENAME_STEM_BONUS` is **1.0**. Full normalized
token-to-filename-stem equality is required. Partial matches and tokens that
appear only elsewhere in the path are rejected. For each matching file, the
bonus is applied only to its highest base-scoring chunk, preventing repeated
chunks or repeated query terms from multiplying the signal.

The mechanism is generic: it contains no GQ04, GQ07, or GQ21 identifiers and
no special cases for `regression` or `i18n`.

## Scope and invariants

- Global retrieval weights are unchanged.
- `explain_code.symbol_boost` remains 2.0.
- Golden data and canonical matcher behavior are unchanged.
- Evaluator semantics and release gates are unchanged.
- The repository assistant remains read-only and exposes no shell execution.
- No UI or Streamlit file changed.

## Implementation summary

The retriever now detects complete equality between normalized query tokens
and filename stems. During base scoring it retains the highest-scoring chunk
for each exact-matching file, then adds the fixed 1.0 bonus to only those
selected chunks before the existing descending sort.

## Test strategy

Focused unit coverage verifies:

1. exact token-to-stem equality receives the bonus;
2. partial tokens receive no bonus;
3. unrelated filenames receive no bonus;
4. repeated query tokens do not multiply the signal; and
5. nonmatches leave the existing score unchanged.

Validation also includes the full tracked public suite, full local workspace,
official evaluation, citation checks, path and secret safety checks, shell
surface inspection, immutable hashes, and diff hygiene.

## Before and after metrics

| Metric | Sprint 1A baseline | Sprint 1B |
| --- | ---: | ---: |
| Retrieval@5 | 19/28 | 22/28 |
| Intent accuracy | 28/30 | 28/30 |
| Citation validity | 30/30 | 30/30 |
| Citation precision | 30/30 | 30/30 |
| Required concept recall | 34/48 | 36/48 |
| Unsupported claims | 0/30 | 0/30 |
| Public tests | 281 passed | 286 passed |

## Query-level outcomes

- **GQ04:** `portfolio/pages/regression.py` reached rank **#4**.
- **GQ21:** `portfolio/i18n.py` reached rank **#5**.
- **GQ07:** `evaluation/search/quality_gates.yaml` unexpectedly improved to
  rank **#3**, producing an additional canonical hit.

## Regression analysis

The final official comparison reported new hits GQ04, GQ07, and GQ21, with no
previously passing query lost. GQ02 remained rank #1 with
`evaluation/search/metrics.py` as its leading result.

## Safety and citation validation

The read-only path boundary, path-escape rejection, and secret-file checks
remain intact. Static inspection found no subprocess or shell-execution surface
under `portfolio/copilot`. Official citation validity and citation precision
both remained 30/30.

## Immutable evaluation hashes

| Artifact | SHA-256 |
| --- | --- |
| Golden dataset | `dafa3510266b9960a17844c4f4322714a0a5879331557fbaaf15df24cbc564f6` |
| Canonical matcher | `a5ef901047a16fffc5fed72526fd2880c5bf62c95da2cfce47d223d5fbe37b9d` |
| Official evaluator | `20394db2835cbc00c3e45d66d5d5f66813ba02f622cec6100851f4d0d5f0725b` |
| Release gates | `0b9230c671c2898561aed92f98979a5aec837a9068ae29eda80d4ae2cbcf0c5b` |

## Known limitations

- Retrieval@5 remains below the configured 0.85 release gate.
- Required concept recall remains below its configured 0.80 release gate.
- Exact filename-stem scoring helps only when the query contains the full stem.
- Turkish phrase normalization and broader compound-token handling remain
  intentionally outside Sprint 1B.

## Next research questions

- Can phrase-level alias expansion improve Turkish quality-gate queries without
  destabilizing existing hits?
- Can compound identifier tokenization recover implementation files without
  introducing broad lexical noise?
- Which remaining misses reflect corpus documentation gaps rather than ranking
  defects?
- Can candidate-window behavior be measured without introducing broad result
  diversification?

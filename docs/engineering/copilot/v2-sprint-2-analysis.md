# AI Project Copilot V2 — Sprint 2 Engineering Report

## Executive summary

Sprint 2 activates existing contiguous multiword entries in `ALIAS_MAP` when
their normalized tokens match a query exactly and in order. The canonical
Retrieval@5 result improved from 22/28 to 23/28. GQ29 is the sole new hit and
no previously passing query regressed. No alias, scoring weight, evaluator,
golden question, matcher, release gate, UI, or Streamlit behavior changed.

## Initial baseline

The approved baseline was commit
`c236debc8671ade7c7dbe5fc3df7cb2c6f342f40` on
`feature/ai-project-copilot-v2-sprint-2`. Retrieval@5 was 22/28, intent
accuracy was 28/30, citation validity and precision were 30/30, required
concept recall was 36/48, and unsupported claims were 0/30. GQ02 ranked the
expected `metrics.py` file first, and `explain_code.symbol_boost` was 2.0.

## Remaining failure inventory

The baseline misses were GQ03, GQ11, GQ12, GQ19, GQ25, and GQ29. After this
change, the remaining misses are GQ03, GQ11, GQ12, GQ19, and GQ25.

## Root-cause taxonomy

- GQ29 was a dormant configuration problem: the exact `pipeline stages`
  phrase existed in `ALIAS_MAP`, but normalization considered aliases only one
  token at a time.
- GQ11 remains a Turkish morphology mismatch: the configured phrase is
  `kalite geçit`, while the query contains the distinct complete token
  `geçitleri`.
- The other misses have independent ranking, intent, corpus, or vocabulary
  causes and were intentionally excluded from this implementation.

## Dormant configured phrase finding

`ALIAS_MAP` already contained multiword keys and their approved expansions.
Those entries were unreachable as phrases because the existing normalization
loop performed lookups on a set of individual ASCII tokens. Sprint 2 makes the
configured phrases reachable without changing their keys or values.

## Approved hypothesis and implementation design

A small helper tokenizes the normalized query and each configured alias key,
then compares contiguous token windows. Only keys containing at least two
tokens participate. A successful match contributes only the expansion tokens
already stored in `ALIAS_MAP`.

The legacy single-token normalization loop is unchanged. Phrase expansions are
merged into the existing set, so repeated or overlapping phrases cannot
multiply tokens or scores.

## Token-boundary and contiguity rules

A phrase activates only when all configured tokens occur contiguously, in the
configured order, with complete Unicode-aware token equality. Separated,
reversed, single-token, and partial-substring occurrences are rejected. There
is no substring matching, prefix matching, stemming, or morphological rewrite.

## Tests added

Focused tests cover contiguous activation, noncontiguous and reversed tokens,
partial-substring rejection, repeated phrases, overlapping expansion
deduplication, and the Turkish morphology boundary that intentionally keeps
GQ11 blocked. Existing tests continue to cover unchanged single-token aliases
and unrelated queries.

## Before and after metrics

| Metric | Baseline | Sprint 2 |
| --- | ---: | ---: |
| Retrieval@5 | 22/28 | 23/28 |
| Intent accuracy | 28/30 | 28/30 |
| Citation validity | 30/30 | 30/30 |
| Citation precision | 30/30 | 30/30 |
| Required concept recall | 36/48 | 37/48 |
| Unsupported claims | 0/30 | 0/30 |
| Public tracked tests | 286 passed | 293 passed |

## Query-level outcomes

- GQ29: the expected `portfolio/search_index.py` moved from outside the top
  five to rank #3. This is the only new hit.
- GQ11: the expected files remain outside the top five both before and after.
  Strict token equality correctly prevents `kalite geçit` from matching
  `kalite geçitleri`.
- GQ02: `evaluation/search/metrics.py` remains rank #1.
- Regressions: none.

## Safety, citation, and immutable artifacts

The full tracked public test suite passes with 293 tests. It includes the
existing path, secret, read-only, citation, and portfolio integrity coverage.
Static inspection found no subprocess or shell-execution surface added under
`portfolio/copilot`. Official citation validity and precision remain 30/30.

| Artifact | SHA-256 |
| --- | --- |
| Golden dataset | `dafa3510266b9960a17844c4f4322714a0a5879331557fbaaf15df24cbc564f6` |
| Canonical matcher | `a5ef901047a16fffc5fed72526fd2880c5bf62c95da2cfce47d223d5fbe37b9d` |
| Official evaluator | `20394db2835cbc00c3e45d66d5d5f66813ba02f622cec6100851f4d0d5f0725b` |
| Release gates | `0b9230c671c2898561aed92f98979a5aec837a9068ae29eda80d4ae2cbcf0c5b` |

## Workspace validation note

Repository-root pytest collection is not a clean release signal in the current
workspace: it reported 438 passed, 8 failed, and 1 error. The failures are
outside Sprint 2 and arise from untracked Group C embedding/graph tests, absent
local semantic-model assets, and collection of a browser script without its
`page` fixture. No Group C or unrelated production file was changed. The
isolated tracked checkout passes 293/293 tests.

## Known limitations

GQ11 cannot be recovered under the approved constraints. Its inflected Turkish
token `geçitleri` is not exactly equal to the configured phrase token `geçit`.
Recovering it would require a new alias, prefix/substring behavior, or Turkish
morphological normalization, all explicitly excluded from Sprint 2.

Retrieval@5 and required concept recall remain below their configured release
gates. README metrics were not updated because full-workspace validation was
not clean.

## Rejected alternatives

- Substring and prefix matching were rejected because they violate complete
  token boundaries.
- Adding `kalite geçitleri` was rejected because no new aliases are allowed.
- Turkish stemming was rejected as a broader tokenizer change.
- Global weights, target paths, query IDs, penalties, and diversification were
  rejected as higher-risk or out of scope.

## Next research questions

- Can Turkish morphology be handled with a separately approved, bounded design
  that preserves strict lexical precision?
- Which remaining misses reflect corpus evidence gaps rather than ranking?
- Can GQ12's intent mismatch be corrected without changing canonical intent
  behavior for existing hits?

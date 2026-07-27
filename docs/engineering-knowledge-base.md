# Engineering Knowledge Base

Recorded discoveries, patterns, and lessons from the Turkey AI Academy portfolio project.

---

## AHA-001a — BM25 Pre-Slicing Excludes Non-Content Matches

**Date:** 2026-07
**Status:** Confirmed
**Category:** Candidate Selection / Pipeline Architecture

### Symptom
The notebook resource "data_science_midterm.ipynb" did not appear in the top
results for the "notebook" query even though its tag matched perfectly.

### Root Cause
The candidate selection pipeline first computed BM25 scores and sliced to
`top_k * 20` candidates. Only after this sliced list was populated did title,
tag, and product-resource candidate stages add to the set. The notebook resource
had zero BM25 score (its JSON content does not contain the word "notebook"), so
it was excluded from the initial BM25 slice. It was later **re-added** by the
tag-match stage — but in the **original** buggy code (see AHA-001b), the scoring
loop only processed the BM25-sliced subset, so the re-added candidate was never
scored.

### Current Mitigation
The BM25 slice is now only a **first pass** at `top_k * 20` candidates. Title
match, tag match, and product-resource stages add candidates to the same set.
All candidates (from all stages) are scored before the final sort. A tag-matched
resource excluded from the BM25 slice is still caught by the tag stage.

### Why It Was Surprising
The bug was invisible in unit tests with ≤10 documents where all relevant
resources happened to be in the BM25 top-200. With 266 real documents, the
notebook's zero BM25 content score pushed it out of the slice entirely.

### General Engineering Principle
**Multi-stage candidate selection must use union semantics, not pipeline
semantics.** Each stage should add candidates to a shared set. No stage should
replace or filter the output of a previous stage. Content-only first-pass
selection naturally misses documents that match via metadata.

### Regression Protection
- The `candidate_indices = set()` (line 567) is updated by all four stages.
- Tag-match stage (line 591-597) catches non-content matches.
- Product-resource stage (line 599-606) catches resource-type matches.
- Score stage (line 710-712) processes all candidate indices before sorting.

---

## AHA-001b — Break-Before-Sort: Only Sliced Candidates Scored

**Date:** 2026-07
**Status:** Confirmed (Fixed)
**Category:** Control Flow / Algorithm

### Symptom
When the notebook was re-added to the candidate set by the tag-match stage, it
did not appear in the final results. Even the correct title_weight/tag_score
adjustments had no effect.

### Root Cause
The historical code computed field-weighted scores for only the first `top_k`
candidates, then sorted and returned them:

```
# OLD (buggy):
candidates = list(candidate_indices)[:top_k]  # BUG: slice before scoring
results = []
for idx in candidates:
    score = compute_field_weighted_score(doc, query)
    results.append(SearchResult(...))
results.sort(key=lambda r: r.score, reverse=True)
```

The `:top_k` slice on the unordered list of candidate indices silently dropped
all tag-matched resources that happened to be at the end of the iterated set.
Because `candidate_indices` is a `set()` (unordered), which resources were
scored was non-deterministic. Some searches would show the notebook, others
would not.

### Why It Was Surprising
The bug appeared intermittent — sometimes the notebook appeared, sometimes not.
The root cause was masked by the non-deterministic iteration order of Python sets.
Tests that happened to get lucky (notebook in the first 10 iterated items) passed.

### General Engineering Principle
**Never slice before sorting in a scoring pipeline.** Always collect all
candidates, score every one with the full formula, then sort and slice. The
slice belongs at the very end, not the middle.

### Regression Protection
- Line 710-712 now score ALL candidates, sort, then slice:
  ```python
  results.sort(key=lambda r: r.score, reverse=True)
  return results[:top_k]
  ```
- No intermediate slicing exists between line 608 (candidate list) and line 710.
- Tests verify that tag-matched resources appear at their correct rank.

---

## AHA-002 — Type Boost Cannot Create Relevance

**Date:** 2026-07
**Status:** Confirmed
**Category:** Scoring / Ranking

### Symptom
Searching for "notebook" returned source_code files in the top results, because
the catch-all rule added all source_code documents as candidates with a minimal
type_boost of 0.1. Combined with title matching on infrastructure files named
"Notebook Status", these scored above the actual notebook.

### Root Cause
The type_boost was applied unconditionally — any document in the candidate set
received the boost regardless of whether it had any relevance signal (content,
title, or tag match). This meant irrelevant documents could accumulate enough
score from type_boost alone to outrank relevant documents.

### General Engineering Principle
**Type boost should amplify existing relevance, not create it.** A document
with zero content, title, and tag match should not receive a significant type
boost. Gate the boost behind a relevance check.

### Regression Protection
- The relevance gate (`has_relevance`) was added: full type_boost only applies
  when base_score > 0 OR title_score > 0 OR tag_score > 0.
- Catch-all candidates receive only 0.1 type_boost (below noise threshold).
- Gate A test verifies notebook ranks #1 for "notebook" query.

---

## AHA-003 — Source Code Penalty Must Compete With Title+Tag Signals

**Date:** 2026-07
**Status:** Confirmed
**Category:** Scoring / Penalty Design

### Symptom
Source_code infrastructure files (e.g., "Notebook Status") with strong title and
tag matches outranked actual product resources (e.g., the notebook
"data_science_midterm.ipynb") for product queries.

### Root Cause
Source_code files get a title match via infrastructure page titles and a tag
match via their descriptive tags. Without a penalty, these signals gave them
scores of ~4.75 (title_score 1.5, title_exact 1.0, tag_score 2.0, base_score
0.25), while the notebook only scored ~4.0 (tag_score 2.0, type_boost 2.0).
The binary penalty (0.8 only without relevance) was insufficient because
source_code files WITH relevance signals still outranked product resources.

### Scoring Formula
The penalty is a **subtraction** from the combined score:

```
combined = (base × 0.5) + (title_score × title_weight) + (tag_score × 2.0)
         + type_boost + (title_exact × title_exact_boost)
         - i18n_penalty - source_code_penalty
```

Current values:

| Match type | source_code_penalty | Effect |
|------------|-------------------|--------|
| No relevance (catch-all only) | 0.8 | Pushes score negative → filtered out |
| Has relevance (content/title/tag) | 1.5 | Reduces score but may remain positive |

Source_code with a relevance signal receives a **larger** penalty (1.5 > 0.8)
because it competes more directly with product resources via title and tag
signals. The larger penalty is necessary to ensure product resources outrank
infrastructure even when infrastructure has strong title+tag matches.

### Numerical Example (Gate A — "notebook")
**Source_code "Notebook Status"** (has relevance: title+tag match):
```combined = 0.25 + 1.5×1.0 + 1.0×2.0 + 0 + 1.0×1.0 - 0 - 1.5 = 3.25```

**Notebook "data_science_midterm.ipynb"** (has relevance: tag match):
```combined = 0 + 0 + 1.0×2.0 + 2.0 + 0 - 0 - 0 = 4.00```

**Irrelevant catch-all source_code** (no relevance, matched via catch-all rule):
```combined = 0 + 0 + 0 + 0.1 + 0 - 0 - 0.8 = -0.70 → filtered out```

Result: product resource (4.00) > relevant source_code (3.25) > irrelevant source_code (filtered) ✓

### General Engineering Principle
**Source_code penalties must be proportional to the competing signals.**
A penalty that only activates for no-relevance matches is insufficient when
source_code can score via the same title/tag channels as product resources.
Penalize relevant source_code more heavily (1.5 > 0.8) because its
title+tag baseline is higher and it directly competes with product resources.
Penalize catch-all source_code lightly (0.8) because even a small subtraction
pushes its near-zero baseline below the filter threshold.

### Regression Protection
- Source_code penalty: 0.8 (no relevance) / 1.5 (has relevance).
- Gate A: notebook ranks #1 for "notebook" (4.00 > 3.25).
- Gate C: sentiment product ranks #1 for "sentiment" (21.04 > 1.14).
- Gate J: meaningful resource ranks #1 for "grid search" (10.01 > i18n absent).

---

## AHA-004 — Metadata Quality Is Part of Ranking Quality

**Date:** 2026-07
**Status:** Confirmed
**Category:** Data Quality / Title Extraction

### Symptom
Some source_code documents had `,` (comma) as their title in search results,
appearing as "1. , (source_code)" — clearly wrong to users.

### Root Cause
The `_extract_title()` function parsed triple-quoted docstrings but failed to
handle the closing `"""` line when it was followed by a comma. The regex or
string matching captured `""",\n` and interpreted the comma as the title content.

### Impact
- Malformed titles appeared in search results, degrading UX trust.
- Clicking a result with title "," gives no information about the resource.
- The issue was invisible in tests because tests used synthetic docstrings
  without trailing commas.

### General Engineering Principle
**Title extraction is a critical-path function.** Every document's title is
displayed to users and used for ranking. Edge cases in parsing (f-strings,
closing quotes with punctuation, empty docstrings) must be explicitly tested.

### Regression Protection
- `test_s3_extract_title_no_comma` — verifies normal docstrings extract correctly.
- `test_s3_extract_title_fstring_ignored` — verifies f-strings fall back to path stem.
- `test_s3_extract_title_closing_comma_ignored` — verifies closing comma is rejected.
- The `_extract_title()` function now explicitly rejects strings ending with
  `,;)]` and lines that are only closing triple-quotes.

---

## AHA-005 — Function Name Typos Crash at Runtime, Not Import Time

**Date:** 2026-07
**Status:** Confirmed
**Category:** Error Handling / Code Quality

### Symptom
The search workspace page showed only the first result, then displayed
"Bu sayfa geçici olarak görüntülenemiyor" (This page is temporarily unavailable).
Streamlit logs showed `NameError: name 'repository_relative' is not defined`.

### Root Cause
Line 306 of `search.py` called `repository_relative(payload)` but the function
was imported as `repository_relative_path`. The NameError was only triggered
when the "Copy Path" action button was rendered, which happened after the first
result card — so the first result displayed fine but all subsequent results crashed.

### Why It Was Surprising
The error was in a rarely-exercised code path (the "Copy Path" action button).
It didn't affect the search logic or the first result. Unit tests never rendered
the full UI, so the error was invisible until browser verification.

### General Engineering Principle
**Runtime errors in rendering code can silently truncate output.** A single
exception in a loop iteration can prevent all subsequent iterations from executing.
Always verify the full output, not just the first element.

### Regression Protection
- The function name was corrected to `repository_relative_path`.
- Browser verification (Phase 3) now checks that all 20 results render
  (not just the first one).
- The Streamlit error log is checked for NameError/ImportError after every search.

---

## Classification Key

- **New to this project**: The discovery was specific to this codebase's architecture.
- **Known industry principle**: The discovery validates a well-known software engineering principle.
- **Experimental hypothesis**: The discovery needs further validation.

AHA-001: Known industry principle (eager evaluation before selection)
AHA-002: Known industry principle (boost vs. create relevance)
AHA-003: New to this project (tiered penalties — relevant source_code penalized MORE than catch-all because baseline scores differ)
AHA-004: Known industry principle (garbage in, garbage out for metadata)
AHA-005: Known industry principle (fail-fast, full-path testing)

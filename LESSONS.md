# Evidence-Backed Engineering Lessons

## LESSON-0001 — Persist preprocessing with models

- Status/confidence: confirmed
- Source: churn, housing, NLP; TASK-0002/TASK-0003; ADR-0001
- Observation: training pipelines persist preprocessing and model artifacts.
- Lesson: runtime should load the evaluated transformation/model contract rather
  than reconstruct it ad hoc.
- Boundary: artifact compatibility and missing files still require safe failure.
- Evidence: project training scripts and loaders.

## LESSON-0002 — Evaluate gains against every prior hit

- Status/confidence: confirmed
- Source: Copilot; TASK-0010–TASK-0012; ADR-0003
- Observation: several broad candidates improved a target but regressed others.
- Lesson: a retrieval improvement is incomplete without explicit regression
  accounting.
- Boundary: benchmark health and corpus quality must also be audited.

## LESSON-0003 — Exact filename evidence can beat broad tuning

- Status/confidence: confirmed
- Source: Copilot Sprint 1B; EXP-0002
- Observation: one per-file exact stem signal recovered three hits.
- Lesson: narrow structural evidence can outperform global weight changes.
- Boundary: only full equality qualifies; repeated chunks must not multiply it.

## LESSON-0004 — Dormant configuration is not behavior

- Status/confidence: confirmed
- Source: Copilot Sprint 2; EXP-0003
- Observation: multiword aliases existed but token-by-token normalization could
  not activate them.
- Lesson: configuration needs reachability and boundary tests.
- Boundary: no substring, prefix, or unapproved morphology.

## LESSON-0005 — Intent errors can look like ranking errors

- Status/confidence: confirmed
- Source: GQ12; TASK-0012; FAIL-0003
- Observation: accepted files were #6/#7 under the wrong intent and entered the
  top five after routing alone changed.
- Lesson: inspect semantic routing before adjusting retrieval scoring.
- Boundary: explicit declaration queries remain locate-symbol requests.

## LESSON-0006 — Broad evidence propagation can regress unrelated queries

- Status/confidence: confirmed
- Source: Sprint 3 counterfactuals
- Observation: file/chunk propagation produced regressions.
- Lesson: measure affected-query surface and reject gains that duplicate broad
  scoring mechanisms.

## LESSON-0007 — Missing model assets must fail safely

- Status/confidence: confirmed
- Source: Trendyol semantic runtime; FAIL-0001
- Observation: ignored model snapshots are not available in fresh checkouts.
- Lesson: asset availability must be explicit and must not trigger hidden
  downloads or fabricated metrics.

## LESSON-0008 — Plans are not completed systems

- Status/confidence: confirmed
- Source: data-science final, clustering, deployment pages
- Observation: plans/templates/pages exist without completed model evidence.
- Lesson: documentation status must follow executable and evaluation evidence.

## LESSON-0009 — Separate evidence from inference

- Status/confidence: confirmed current standard
- Source: Knowledge System V1; TASK-0013
- Observation: Git proves state and dates but not private motivation.
- Lesson: label unknowns and author-confirmation needs instead of smoothing gaps.

## LESSON-0010 — Protect evaluation assets

- Status/confidence: confirmed
- Source: Copilot evaluation; ADR-0003
- Observation: golden, matcher, evaluator, and gates define the benchmark.
- Lesson: never modify the measuring system to validate a production change.

## LESSON-0011 — Prefer the smallest general rule

- Status/confidence: confirmed
- Source: Copilot V2 experiments
- Observation: exact stems, exact phrases, and intent precedence improved metrics
  without query IDs or target paths.
- Lesson: narrow general behavior is safer than benchmark-specific repair.


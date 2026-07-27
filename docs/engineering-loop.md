# Adaptive Multi-Perspective Engineering Loop

## Purpose

A structured methodology for building, verifying, and closing software milestones
with evidence-backed completion claims. Designed for solo developers working on
complex features where correctness must be verifiable.

## Workflow

### 1. Plan
- Review the feature from 9 perspectives: end user, hiring manager, product manager,
  search engineer, software architect, QA engineer, UX/accessibility, security, maintainer.
- For each perspective: one expected benefit, one critical risk, one measurable acceptance condition.
- No code changes during planning.

### 2. Multi-Perspective Review
- Validate the plan against the actual codebase state.
- Identify gaps between intended behavior and actual behavior.

### 3. Implement Smallest Viable Change
- Make the minimal change that addresses the identified issue.
- Never apply query-specific or test-specific hardcoding.
- Every fix must be generalizable.

### 4. Self-Review
- Read the diff. Verify no secrets, no hardcoded paths, no dead code.
- Confirm the change follows existing code conventions.

### 5. Evidence Collection
- Run the full test suite.
- Verify behavior in a real browser (not just unit tests).
- Capture screenshots as visual evidence.
- Record exact commands, outputs, and timestamps.

### 6. Contradiction Audit
- For every claim in the completion report, provide matching evidence.
- Any claim without evidence is a contradiction.
- Any contradiction means the milestone is NOT READY.

### 7. Root-Cause Analysis
- When a gate fails, identify the exact root cause (not symptoms).
- Distinguish between algorithm problems, control-flow problems, and data problems.

### 8. Smallest Generalizable Fix
- Apply the minimal change that fixes the root cause.
- The fix must not introduce new regressions.
- The fix must work for all inputs, not just the failing case.

### 9. Regression Testing
- Re-run ALL gates after every fix (not just the failing one).
- Re-run the full test suite.
- Verify no new warnings or errors in application logs.

### 10. Standardization
- Update documentation to reflect the new behavior.
- Record AHA discoveries in the knowledge base.

### 11. Discover
- After the milestone is stable, review for future improvements.
- Classify each finding: Adopt Now, Backlog, Reject, or Requires Experiment.

### 12. AHA Detector
- What assumption was disproved?
- What bug looked like an algorithm problem but was actually a control-flow problem?
- What local fix can become a general design rule?
- What result would not have been discovered through tests alone?

### 13. Stop Condition
- All gates pass with fresh evidence.
- All claims are backed by evidence.
- No contradictions exist.
- Maximum 3 repair iterations (then escalate).

## Mandatory Rules

- **Completion claims require fresh evidence.** Previous results are stale.
- **Browser behavior outranks written claims.** If the browser shows it differently, the browser wins.
- **Tests must validate behavior, not implementation trivia.** Avoid testing private methods or exact string matches.
- **No hardcoded query-specific fixes.** All fixes must be generalizable.
- **Runtime artifacts must remain untracked.** Index caches, JSONL stores, screenshots are gitignored.
- **Repeated failures trigger root-cause analysis.** After 2 failures on the same gate, stop and analyze.
- **Maximum repair iterations: 3.** After 3 failed attempts, escalate to a different approach.
- **Unsupported features must not appear in the UI.** No dead buttons, no nonfunctional actions.
- **New methods require measurable improvement.** Don't add complexity without proven benefit.

## Iteration Protocol

Each iteration:
1. Run ALL gates (not just the failing one).
2. Capture evidence.
3. Identify the smallest failing gate.
4. Analyze root cause.
5. Apply the smallest generalizable fix.
6. Re-run ALL gates.
7. If fixed, continue to next gate. If not, repeat from step 1.

Maximum 3 iterations. If iteration 3 fails, the milestone is NOT READY and
requires architectural intervention.

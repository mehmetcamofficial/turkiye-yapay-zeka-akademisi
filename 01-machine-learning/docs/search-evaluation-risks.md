# Search Evaluation — Anti-Regression Risk Analysis

## Risk: Golden query set overfits to current scoring formula
- **Severity**: Medium
- **Mitigation**: Add new golden queries from real user search patterns; periodically review relevance grades
- **Trigger**: NDCG improves on golden set but degrades on holdout queries

## Risk: Quality gates too permissive (false sense of security)
- **Severity**: High
- **Mitigation**: Gates set from actual baseline metrics; tighten as search quality improves
- **Trigger**: All gates pass despite visible ranking quality issues

## Risk: Quality gates too strict (block legitimate improvements)
- **Severity**: Low
- **Mitigation**: Gate thresholds documented and adjustable via YAML; track delta not just pass/fail
- **Trigger**: Improved ranking fails gate due to off-target metric

## Risk: Relevance grades subjective or inconsistent
- **Severity**: Medium
- **Mitigation**: Each golden query has documented intent; grades use 0-3 scale with explicit rubric
- **Trigger**: Two evaluators assign different grades to the same query-resource pair

## Risk: Evaluation depends on fixed baseline snapshot
- **Severity**: Low
- **Mitigation**: Baseline is a JSON file pinned to commit; re-freeze after intentional improvements
- **Trigger**: Baseline metrics drift after index rebuild

## Risk: Tokenization changes affect cross-lingual queries
- **Severity**: Medium
- **Mitigation**: Query set includes both Turkish and English queries; monitor by language
- **Trigger**: Turkish NDCG diverges from English NDCG

## Risk: Must-include resources vanish from top-K
- **Severity**: High
- **Mitigation**: Must-include gate is a hard gate; failure blocks deployment
- **Trigger**: Key resources (model:churn, model:nlp) drop below top-10

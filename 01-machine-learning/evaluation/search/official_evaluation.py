#!/usr/bin/env python3
"""
Official Evaluation Command for AI Project Copilot V1.
Single command that produces all official metrics.
"""

from __future__ import annotations

import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime

# Ensure local imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from portfolio.copilot.indexer import index_repository
from portfolio.copilot.config import REPO_ROOT
from portfolio.copilot.intent import classify_intent
from portfolio.copilot.retriever import retrieve, RetrievalConfig
from portfolio.copilot.answer import generate_answer
from portfolio.copilot.citation import validate_citation
from portfolio.copilot.schema import CopilotConfig

# Import golden dataset and canonical matcher
sys.path.insert(0, str(Path(__file__).parent))
from canonical_match import check_retrieval_hit_canonical, MatchTarget, TargetType
from real_evaluation import (
    load_golden_questions,
    _extract_concepts_from_answer,
    _check_citation_support,
)

OFFICIAL_GATES = {
    "retrieval_hit_rate@5": {"operator": ">=", "threshold": 0.85},
    "citation_validity": {"operator": "==", "threshold": 1.00},
    "citation_precision": {"operator": ">=", "threshold": 0.90},
    "required_concept_recall": {"operator": ">=", "threshold": 0.80},
    "unsupported_claim_rate": {"operator": "<=", "threshold": 0.02},
    "no_evidence_refusal_accuracy": {"operator": ">=", "threshold": 0.90},
    "intent_classification_accuracy": {"operator": ">=", "threshold": 0.80},
}


def evaluate_gate(value: float, gate_spec: dict) -> str:
    op = gate_spec["operator"]
    thresh = gate_spec["threshold"]
    if op == ">=":
        return "PASS" if value >= thresh else "FAIL"
    elif op == "<=":
        return "PASS" if value <= thresh else "FAIL"
    elif op == "==":
        return "PASS" if abs(value - thresh) < 1e-9 else "FAIL"
    return "UNKNOWN"


def main():
    script_dir = Path(__file__).parent
    ml_root = script_dir.parent.parent
    output_path = ml_root / "acceptance_project_copilot" / "retrieval_truth_audit" / "official_results.json"
    manifest_path = ml_root / "acceptance_project_copilot" / "retrieval_truth_audit" / "run_manifest.json"

    # The manifest is optional run provenance, never an evaluation input.
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {"source": "runtime"}

    # Build/load index
    print("[1/4] Building production index...")
    config = CopilotConfig()
    chunks = index_repository(REPO_ROOT, config)
    manifest["index_fingerprint"] = str(len(chunks))

    # Load golden questions
    print("[2/4] Loading golden questions...")
    questions = load_golden_questions()

    # Run production pipeline
    print("[3/4] Running production evaluation...")
    results = []
    retrieval_hits = 0
    retrieval_applicable_count = 0
    intent_correct_count = 0
    citation_valid_count = 0
    citation_precision_count = 0
    concept_numerator = 0
    concept_denominator = 0
    unsupported_claims = 0
    total_claims = 0
    refusal_correct = 0
    refusal_total = 0

    for q in questions:
        qid = q["id"]
        question_text = q["question"]
        expected_intent = q["expected_intent"]
        expected_files = q["expected_files"]
        required_concepts = q["required_concepts"]
        answerability = q.get("answerability", "answerable")
        expected_behavior = q.get("expected_behavior", "answer_with_evidence")

        # Production classify_intent
        predicted_intent = classify_intent(question_text)
        intent_signals = []  # Could be extracted from classifier
        intent_correct = predicted_intent == expected_intent
        if intent_correct:
            intent_correct_count += 1

        # Production retrieve
        retrieval_config = RetrievalConfig(
            query_intent=predicted_intent,
            max_results=10,
            min_score=0.0,
        )
        retrieved_chunks = retrieve(question_text, chunks, retrieval_config)
        top5_files = []
        seen = set()
        for c in retrieved_chunks:
            if c.file_path not in seen:
                seen.add(c.file_path)
                top5_files.append(c.file_path)
            if len(top5_files) >= 5:
                break

        # Canonical retrieval hit
        match_result = check_retrieval_hit_canonical(expected_files, top5_files, chunks)
        retrieval_hit = match_result.hit

        # Determine if applicable for retrieval metric
        is_retrieval_applicable = (answerability != "unsupported" and expected_files and expected_behavior != "refuse_no_evidence")
        if is_retrieval_applicable:
            retrieval_applicable_count += 1
            if retrieval_hit:
                retrieval_hits += 1

        # Production generate_answer
        answer = generate_answer(
            question_text,
            retrieved_chunks,
            mode="extractive",
            intent=predicted_intent,
        )

        # Production citation validation
        citations = answer.citations
        valid_citations = [c for c in citations if validate_citation(c, REPO_ROOT)]
        citation_valid = len(valid_citations) == len(citations) if citations else True
        if citation_valid:
            citation_valid_count += 1

        citation_support = _check_citation_support(answer, retrieved_chunks, question_text)
        if citation_support:
            citation_precision_count += 1

        # Concept recall
        concepts_found = _extract_concepts_from_answer(answer.direct_answer, retrieved_chunks)
        concept_matches = [c for c in required_concepts if c in concepts_found]
        concept_numerator += len(concept_matches)
        concept_denominator += len(required_concepts)

        # Unsupported claim rate
        is_unsupported = answer.unsupported
        if answerability != "unsupported" and is_unsupported:
            unsupported_claims += 1
        if answerability != "unsupported":
            total_claims += 1

        # No-evidence refusal accuracy
        if expected_behavior == "refuse_no_evidence":
            refusal_total += 1
            if is_unsupported:
                refusal_correct += 1

        results.append({
            "id": qid,
            "question": question_text,
            "expected": {
                "intent": expected_intent,
                "files": expected_files,
                "required_concepts": required_concepts,
                "answerability": answerability,
                "expected_behavior": expected_behavior,
            },
            "actual": {
                "predicted_intent": predicted_intent,
                "intent_signals": intent_signals,
                "retrieved_files_top5": top5_files,
                "retrieved_chunks_count": len(retrieved_chunks),
                "answer": answer.direct_answer[:500],
                "answer_confidence": answer.confidence,
                "citations": [{"file_path": c.file_path, "start_line": c.start_line, "end_line": c.end_line} for c in citations],
                "concepts_found": concepts_found,
                "unsupported": is_unsupported,
            },
            "evaluation": {
                "retrieval_hit": retrieval_hit,
                "intent_correct": intent_correct,
                "citation_valid": citation_valid,
                "citation_support": citation_support,
                "concept_recall": len(concept_matches) / len(required_concepts) if required_concepts else 0.0,
                "concept_matches": concept_matches,
                "concept_missing": [c for c in required_concepts if c not in concepts_found],
            },
        })

    # Compute metrics
    hit_rate = retrieval_hits / retrieval_applicable_count if retrieval_applicable_count else 0.0
    intent_acc = intent_correct_count / len(questions)
    citation_val = citation_valid_count / len(questions)
    citation_prec = citation_precision_count / len(questions)
    concept_rec = concept_numerator / concept_denominator if concept_denominator else 0.0
    unsupported_rate = unsupported_claims / total_claims if total_claims else 0.0

    if refusal_total > 0:
        refusal_acc = refusal_correct / refusal_total
        refusal_status = evaluate_gate(refusal_acc, OFFICIAL_GATES["no_evidence_refusal_accuracy"])
    else:
        refusal_acc = None
        refusal_status = "NOT_EVALUABLE"

    metrics = {
        "retrieval_hit_rate_at_5": {
            "numerator": retrieval_hits,
            "denominator": retrieval_applicable_count,
            "value": round(hit_rate, 4),
            "gate": 0.85,
            "operator": ">=",
            "status": evaluate_gate(hit_rate, OFFICIAL_GATES["retrieval_hit_rate@5"]),
        },
        "intent_classification_accuracy": {
            "numerator": intent_correct_count,
            "denominator": len(questions),
            "value": round(intent_acc, 4),
            "gate": 0.80,
            "operator": ">=",
            "status": evaluate_gate(intent_acc, OFFICIAL_GATES["intent_classification_accuracy"]),
        },
        "citation_validity": {
            "numerator": citation_valid_count,
            "denominator": len(questions),
            "value": round(citation_val, 4),
            "gate": 1.00,
            "operator": "==",
            "status": evaluate_gate(citation_val, OFFICIAL_GATES["citation_validity"]),
        },
        "citation_precision": {
            "numerator": citation_precision_count,
            "denominator": len(questions),
            "value": round(citation_prec, 4),
            "gate": 0.90,
            "operator": ">=",
            "status": evaluate_gate(citation_prec, OFFICIAL_GATES["citation_precision"]),
        },
        "required_concept_recall": {
            "numerator": concept_numerator,
            "denominator": concept_denominator,
            "value": round(concept_rec, 4),
            "gate": 0.80,
            "operator": ">=",
            "status": evaluate_gate(concept_rec, OFFICIAL_GATES["required_concept_recall"]),
        },
        "unsupported_claim_rate": {
            "numerator": unsupported_claims,
            "denominator": total_claims,
            "value": round(unsupported_rate, 4),
            "gate": 0.02,
            "operator": "<=",
            "status": evaluate_gate(unsupported_rate, OFFICIAL_GATES["unsupported_claim_rate"]),
        },
        "no_evidence_refusal_accuracy": {
            "numerator": refusal_correct,
            "denominator": refusal_total,
            "value": round(refusal_acc, 4) if refusal_acc is not None else None,
            "gate": 0.90,
            "operator": ">=",
            "status": refusal_status,
        },
    }

    # Population definitions
    retrieval_excluded = [r["id"] for r in results if r["expected"]["answerability"] == "unsupported" or not r["expected"]["files"] or r["expected"]["expected_behavior"] == "refuse_no_evidence"]
    retrieval_included = [r["id"] for r in results if r["id"] not in retrieval_excluded]
    intent_excluded = [r["id"] for r in results if not r["expected"]["intent"]]
    concept_excluded = [r["id"] for r in results if not r["expected"]["required_concepts"]]
    refusal_excluded = [r["id"] for r in results if r["expected"]["expected_behavior"] != "refuse_no_evidence"]

    population = {
        "retrieval_hit_rate_at_5": {
            "included_ids": retrieval_included,
            "excluded_ids": retrieval_excluded,
            "exclusion_reasons": {qid: "unsupported or no evidence targets or refusal" for qid in retrieval_excluded},
            "numerator": retrieval_hits,
            "denominator": retrieval_applicable_count,
        },
        "intent_classification_accuracy": {
            "included_ids": [r["id"] for r in results if r["id"] not in intent_excluded],
            "excluded_ids": intent_excluded,
            "exclusion_reasons": {},
        },
        "required_concept_recall": {
            "included_ids": [r["id"] for r in results if r["id"] not in concept_excluded],
            "excluded_ids": concept_excluded,
            "exclusion_reasons": {qid: "no required concepts" for qid in concept_excluded},
        },
        "no_evidence_refusal_accuracy": {
            "included_ids": [r["id"] for r in results if r["id"] not in refusal_excluded],
            "excluded_ids": refusal_excluded,
            "exclusion_reasons": {qid: "not labeled refuse_no_evidence" for qid in refusal_excluded},
            "population_empty": refusal_total == 0,
        },
    }

    output = {
        "run_manifest": manifest,
        "population": population,
        "metrics": metrics,
        "questions": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n[4/4] Official results saved to: {output_path}")

    # Print summary
    print("\n" + "="*60)
    print("OFFICIAL METRICS")
    print("="*60)
    for name, m in metrics.items():
        val_str = f"{m['value']:.4f}" if m['value'] is not None else "N/A"
        print(f"  {name}: {m['numerator']}/{m['denominator']} = {val_str} | Gate: {m['operator']} {m['gate']} -> {m['status']}")
    print("="*60)

    return output_path


if __name__ == "__main__":
    main()

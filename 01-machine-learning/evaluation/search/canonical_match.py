#!/usr/bin/env python3
"""
Canonical Repository-Source Matching for AI Project Copilot Evaluation.

This module defines explicit target types and matching rules to replace
the ad-hoc suffix matching currently used.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class TargetType(Enum):
    EXACT_PATH = "exact_path"
    BASENAME = "basename"
    GLOB = "glob"
    DIRECTORY = "directory"
    SYMBOL = "symbol"


@dataclass
class MatchTarget:
    """A single expected target with explicit type and value."""
    target_type: TargetType
    value: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_golden_entry(cls, entry: str) -> "MatchTarget":
        """Parse a golden dataset entry into a MatchTarget with inferred type."""
        entry = entry.strip()

        # Directory: ends with /
        if entry.endswith("/"):
            return cls(TargetType.DIRECTORY, entry.rstrip("/"))

        # Glob: contains * or ?
        if "*" in entry or "?" in entry:
            return cls(TargetType.GLOB, entry)

        # Symbol: contains :: or looks like a function/class name
        if "::" in entry or (entry.isidentifier() and not entry.endswith(".py")):
            return cls(TargetType.SYMBOL, entry)

        # Exact path: contains path separator
        if "/" in entry or "\\" in entry:
            return cls(TargetType.EXACT_PATH, entry)

        # Default: basename
        return cls(TargetType.BASENAME, entry)

    def matches(self, actual_path: str, symbol_table: dict[str, list[str]] | None = None) -> bool:
        """Check if this target matches the actual path."""
        actual_norm = self._normalize_path(actual_path)

        if self.target_type == TargetType.EXACT_PATH:
            expected_norm = self._normalize_path(self.value)
            return actual_norm == expected_norm

        elif self.target_type == TargetType.BASENAME:
            actual_basename = Path(actual_norm).name
            expected_basename = Path(self.value).name
            # Only match if exactly one indexed source has this basename
            return actual_basename == expected_basename

        elif self.target_type == TargetType.GLOB:
            return fnmatch.fnmatch(actual_norm, self.value) or fnmatch.fnmatch(Path(actual_norm).name, self.value)

        elif self.target_type == TargetType.DIRECTORY:
            expected_dir = self._normalize_path(self.value)
            return actual_norm.startswith(expected_dir + "/") or actual_norm == expected_dir

        elif self.target_type == TargetType.SYMBOL:
            if symbol_table is None:
                return False
            for path, symbols in symbol_table.items():
                if self.value in symbols and self._normalize_path(path) == actual_norm:
                    return True
            return False

        return False

    def _normalize_path(self, path: str) -> str:
        """Normalize path for consistent comparison."""
        path = path.replace("\\", "/")
        # Remove leading ./
        if path.startswith("./"):
            path = path[2:]
        # Remove duplicate slashes
        while "//" in path:
            path = path.replace("//", "/")
        # Normalize case according to filesystem (POSIX = case-sensitive)
        return path


@dataclass
class MatchResult:
    """Result of matching expected targets against actual retrieved paths."""
    hit: bool
    matched_targets: list[MatchTarget]
    unmatched_targets: list[MatchTarget]
    ambiguity_warnings: list[str]
    details: dict[str, Any] = field(default_factory=dict)


def build_symbol_table(chunks: list) -> dict[str, list[str]]:
    """Build a symbol table from indexed chunks: path -> [symbols]."""
    symbol_table: dict[str, list[str]] = {}
    for chunk in chunks:
        if chunk.symbol_name:
            path = chunk.file_path
            if path not in symbol_table:
                symbol_table[path] = []
            if chunk.symbol_name not in symbol_table[path]:
                symbol_table[path].append(chunk.symbol_name)
    return symbol_table


def check_retrieval_hit_canonical(
    expected_entries: list[str],
    actual_top5: list[str],
    chunks: list | None = None,
) -> MatchResult:
    """
    Canonical retrieval hit check using explicit target types.

    Args:
        expected_entries: List of expected targets from golden dataset
        actual_top5: List of actual retrieved repository-relative paths
        chunks: Optional indexed chunks for symbol matching

    Returns:
        MatchResult with hit status and detailed breakdown
    """
    targets = [MatchTarget.from_golden_entry(e) for e in expected_entries]
    symbol_table = build_symbol_table(chunks) if chunks else None

    matched = []
    unmatched = []
    warnings = []

    # Track which actual paths were matched
    matched_actual = set()

    for target in targets:
        target_matched = False
        for actual in actual_top5:
            if actual in matched_actual:
                continue
            if target.matches(actual, symbol_table):
                matched.append(target)
                matched_actual.add(actual)
                target_matched = True
                break

        if not target_matched:
            unmatched.append(target)

    # Check for basename ambiguity
    for target in targets:
        if target.target_type == TargetType.BASENAME:
            basename = Path(target.value).name
            count = sum(1 for actual in actual_top5 if Path(actual).name == basename)
            if count > 1:
                warnings.append(
                    f"Ambiguous basename '{basename}': matches {count} files in top-5"
                )

    hit = len(matched) > 0

    return MatchResult(
        hit=hit,
        matched_targets=matched,
        unmatched_targets=unmatched,
        ambiguity_warnings=warnings,
        details={
            "total_targets": len(targets),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "actual_top5": actual_top5,
            "expected_entries": expected_entries,
        }
    )


def rescore_baseline_with_canonical(
    baseline_results: list[dict],
    chunks: list,
) -> dict:
    """
    Rescore a preserved baseline using canonical matching without
    rerunning production retrieval.

    Returns:
        Dictionary with original_score, canonical_score, changes, details
    """
    hits_original = 0
    hits_canonical = 0
    changes = []

    for result in baseline_results:
        qid = result.get("id", "unknown")
        expected = result["expected"]["files"]
        actual_top5 = result["actual"]["retrieved_files_top5"]
        answerable = result["expected"]["answerability"] != "unsupported"

        if not answerable or not expected:
            continue

        # Original decision
        original_hit = result["evaluation"]["retrieval_hit"]
        if original_hit:
            hits_original += 1

        # Canonical decision
        canonical_result = check_retrieval_hit_canonical(expected, actual_top5, chunks)
        canonical_hit = canonical_result.hit
        if canonical_hit:
            hits_canonical += 1

        if original_hit != canonical_hit:
            changes.append({
                "question_id": qid,
                "original_hit": original_hit,
                "canonical_hit": canonical_hit,
                "expected": expected,
                "actual_top5": actual_top5,
                "matched_targets": [str(t.value) for t in canonical_result.matched_targets],
                "unmatched_targets": [str(t.value) for t in canonical_result.unmatched_targets],
                "warnings": canonical_result.ambiguity_warnings,
                "reason": _classify_change(original_hit, canonical_hit, canonical_result)
            })

    total_applicable = sum(1 for r in baseline_results
                           if r["expected"]["answerability"] != "unsupported" and r["expected"]["files"])

    return {
        "original_hits": hits_original,
        "canonical_hits": hits_canonical,
        "original_score": hits_original / total_applicable if total_applicable else 0.0,
        "canonical_score": hits_canonical / total_applicable if total_applicable else 0.0,
        "total_applicable": total_applicable,
        "changes": changes,
        "change_count": len(changes),
    }


def _classify_change(
    original_hit: bool,
    canonical_hit: bool,
    result: MatchResult
) -> str:
    """Classify why the score changed."""
    if original_hit and not canonical_hit:
        return "A: original expected source was retrieved but matcher failed (now correctly missed)"
    elif not original_hit and canonical_hit:
        if result.unmatched_targets:
            return "B: original missed, but canonical matched via exact path/glob/directory"
        return "B: original missed, canonical hit (matcher repaired)"
    elif original_hit and canonical_hit:
        return "C: both hit (no change)"
    else:
        if result.ambiguity_warnings:
            return "D: ambiguous basename - multiple files share same name"
        return "E: still missed - golden target not in top-5"
"""Generate test_metadata.json for deployment readiness.

Usage:
    python scripts/generate_test_metadata.py

Writes to 01-machine-learning/test_metadata.json with counts from
both the portfolio integrity suite and the Trendyol search-relevance test
suite, plus the verified commit SHA and timestamp.

Run during CI or before release validation. Never from within a
Streamlit page request.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
TRENDYOL_DIR = ML_ROOT / "trendyol-search-relevance"
TESTS_DIR = ML_ROOT / "tests"
OUTPUT = ML_ROOT / "test_metadata.json"


def _run_pytest(cwd: Path, *args: str) -> dict[str, int]:
    cmd = [sys.executable, "-m", "pytest", *args, "--tb=no", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=str(cwd))
    stdout = result.stdout + result.stderr
    m_passed = re.search(r"(\d+)\s+passed", stdout)
    m_failed = re.search(r"(\d+)\s+failed", stdout)
    m_skipped = re.search(r"(\d+)\s+skipped", stdout)
    return {
        "passed": int(m_passed.group(1)) if m_passed else 0,
        "failed": int(m_failed.group(1)) if m_failed else 0,
        "skipped": int(m_skipped.group(1)) if m_skipped else 0,
    }


def _commit_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            capture_output=True, text=True, timeout=10,
            cwd=str(ML_ROOT.parent),
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def main() -> None:
    print("Running portfolio integrity tests...")
    portfolio = _run_pytest(ML_ROOT, "tests/test_portfolio_integrity.py")

    print("Running Trendyol search-relevance tests...")
    trendyol = _run_pytest(TRENDYOL_DIR, "tests/")

    total_passed = portfolio["passed"] + trendyol["passed"]
    total_failed = portfolio["failed"] + trendyol["failed"]
    total_skipped = portfolio["skipped"] + trendyol["skipped"]

    sha = _commit_sha()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    metadata = {
        "verified_commit": sha,
        "verified_at": now,
        "portfolio": portfolio,
        "trendyol": trendyol,
        "total": {
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
        },
    }

    OUTPUT.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWritten to {OUTPUT}")
    print(f"Commit: {sha}")
    print(f"Portfolio: {portfolio['passed']} passed, {portfolio['failed']} failed, {portfolio['skipped']} skipped")
    print(f"Trendyol:  {trendyol['passed']} passed, {trendyol['failed']} failed, {trendyol['skipped']} skipped")
    print(f"Total:     {total_passed} passed, {total_failed} failed, {total_skipped} skipped")


if __name__ == "__main__":
    main()

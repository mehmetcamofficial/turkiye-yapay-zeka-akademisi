from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Evaluation Framework CLI")
    parser.add_argument("--golden", required=True, help="Path to golden_queries.yaml")
    parser.add_argument("--baseline", help="Path to baseline JSON for comparison")
    parser.add_argument("--freeze", help="Output path to freeze baseline JSON")
    parser.add_argument("--top-k", type=int, default=10, help="Top-K for evaluation")
    parser.add_argument("--output", help="Output path for evaluation JSON")
    parser.add_argument("--report", action="store_true", help="Generate markdown report")
    parser.add_argument("--compare", action="store_true", help="Run comparison with baseline")
    parser.add_argument("--self-test", action="store_true", help="Run self-comparison (baseline vs itself)")

    args = parser.parse_args()

    golden_path = Path(args.golden)
    if not golden_path.exists():
        print(f"Error: golden queries file not found: {golden_path}", file=sys.stderr)
        sys.exit(1)

    from portfolio.search_index import get_search_index

    index = get_search_index()
    index.ensure_ready()

    def search_fn(query: str, top_k: int = 10):
        return index.search(query, top_k=top_k)

    from evaluation.search.evaluator import SearchEvaluator
    from evaluation.search.metrics import parse_metrics_report

    evaluator = SearchEvaluator(search_fn=search_fn, golden_path=golden_path, top_k=args.top_k)

    result = evaluator.run()

    if args.freeze:
        evaluator.freeze_baseline(args.freeze, result)
        print(f"Baseline frozen to: {args.freeze}")

    if args.self_test:
        if not args.baseline:
            print("Error: --self-test requires --baseline", file=sys.stderr)
            sys.exit(1)
        from evaluation.search.dataset import load_baseline
        baseline_path = Path(args.baseline)
        if not baseline_path.exists():
            print(f"Error: baseline file not found: {baseline_path}", file=sys.stderr)
            sys.exit(1)
        baseline_data = load_baseline(args.baseline)
        comparison = evaluator.compare_with_baseline(args.baseline, baseline_data)
        metrics_report = comparison.get("metrics_report", {})
        print("=== Self-Comparison Results ===")
        print(f"  RSI: {metrics_report.get('ranking_stability_index', 'N/A')}")
        print(f"  Top-1 unchanged rate: {metrics_report.get('top_1_unchanged_rate', 'N/A')}")
        print(f"  Top-3 Jaccard: {metrics_report.get('top_3_jaccard', 'N/A')}")
        print(f"  Top-10 Jaccard: {metrics_report.get('top_10_jaccard', 'N/A')}")
        print(f"  Changed queries: {metrics_report.get('changed_queries', 'N/A')}")
        print(f"  Improved queries: {metrics_report.get('improved', 'N/A')}")
        print(f"  Regressed queries: {metrics_report.get('regressed', 'N/A')}")
        print(f"  Unchanged queries: {metrics_report.get('unchanged', 'N/A')}")
        print(f"  Largest rank movement: {metrics_report.get('largest_rank_movement', 'N/A')}")
        if args.output:
            out_path = Path(args.output)
            out_path.write_text(json.dumps(comparison, indent=2, default=str))
            print(f"Self-comparison written to: {out_path}")
        return

    if args.compare and args.baseline:
        comparison = evaluator.compare_with_baseline(args.baseline, result)
        if args.output:
            out_path = Path(args.output)
            out_path.write_text(json.dumps(comparison, indent=2, default=str))
            print(f"Comparison written to: {out_path}")
        else:
            print(json.dumps(comparison, indent=2, default=str))
    else:
        if args.report:
            from evaluation.search.report import generate_report

            report = generate_report(result)
            if args.output:
                out_path = Path(args.output)
                out_path.write_text(report)
                print(f"Report written to: {out_path}")
            else:
                print(report)
        else:
            if args.output:
                out_path = Path(args.output)
                out_path.write_text(json.dumps(result, indent=2, default=str))
                print(f"Results written to: {out_path}")
            else:
                print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()

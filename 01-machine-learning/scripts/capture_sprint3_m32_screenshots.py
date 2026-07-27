"""Capture Sprint 3 M3.2 acceptance screenshots using Playwright."""
import json
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

APP_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = APP_DIR / "acceptance_sprint3_m3_2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STREAMLIT_PORT = 8766
BASE_URL = f"http://localhost:{STREAMLIT_PORT}"


def navigate_to_search_intelligence(page):
    """Navigate to the Search Intelligence Evaluation page."""
    page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
    time.sleep(8)

    # Open section selectbox, choose SEARCH INTELLIGENCE (option index 1)
    page.locator('[data-testid="stSelectbox"]').first.click()
    time.sleep(1)
    page.locator('[role="option"]').nth(1).click()
    time.sleep(6)

    # Click Search Intelligence page radio (item index 1 in the radio group)
    radio_group = page.locator('[role="radiogroup"]').nth(1)
    items = radio_group.locator('[data-baseweb="radio"]')
    items.nth(1).click()
    time.sleep(6)


def capture(page, name):
    """Take a full-page screenshot."""
    path = OUT_DIR / name
    page.screenshot(path=str(path), full_page=True)
    print(f"  Captured: {name}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = context.new_page()

        # ── 01: Dashboard — Run Evaluation tab (empty) ──
        print("\n01: Search Intelligence — Run tab (empty)")
        navigate_to_search_intelligence(page)
        capture(page, "01_search_intelligence_run_tab.png")

        # ── 02: Run Evaluation — click button ──
        print("\n02: Search Intelligence — Running evaluation")
        run_btn = page.locator('button:has-text("Değerlendirmeyi Çalıştır")')
        if run_btn.count():
            run_btn.first.click()
            time.sleep(18)
        capture(page, "02_search_intelligence_results.png")

        # ── 03: Quality gates section ──
        print("\n03: Search Intelligence — Quality gates")
        page.evaluate("window.scrollTo(0, 600)")
        time.sleep(2)
        capture(page, "03_search_intelligence_gates.png")

        # ── 04: Per-query breakdown ──
        print("\n04: Search Intelligence — Per-query breakdown")
        page.evaluate("window.scrollTo(0, 1300)")
        time.sleep(2)
        capture(page, "04_search_intelligence_breakdown.png")

        # ── 05: Freeze as baseline ──
        print("\n05: Freeze as baseline")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        freeze_btn = page.locator('button:has-text("Taban Çizgisi Olarak Dondur")')
        if freeze_btn.count():
            freeze_btn.first.click()
            time.sleep(4)
        capture(page, "05_search_intelligence_frozen.png")

        # ── 06: Baseline tab (now filled) ──
        print("\n06: Search Intelligence — Baseline tab")
        baseline_tab = page.locator('button:has-text("Taban Çizgisi")')
        if baseline_tab.count():
            baseline_tab.first.click()
            time.sleep(4)
        capture(page, "06_search_intelligence_baseline.png")

        # ── 07: Golden Queries tab ──
        print("\n07: Search Intelligence — Golden Queries tab")
        golden_tab = page.locator('button:has-text("Altın Sorgular")')
        if golden_tab.count():
            golden_tab.first.click()
            time.sleep(4)
        capture(page, "07_search_intelligence_golden.png")

        # ── 08: About tab ──
        print("\n08: Search Intelligence — About tab")
        about_tab = page.locator('button:has-text("Hakkında")')
        if about_tab.count():
            about_tab.first.click()
            time.sleep(3)
        capture(page, "08_search_intelligence_about.png")

        # ── 09: Search Intelligence — Golden with expanded details ──
        print("\n09: Search Intelligence — Dataset details expanded")
        golden_tab2 = page.locator('button:has-text("Altın Sorgular")')
        if golden_tab2.count():
            golden_tab2.first.click()
            time.sleep(2)
        expander = page.locator('summary:has-text("Dataset Details")')
        if expander.count():
            expander.first.click()
            time.sleep(2)
        capture(page, "09_search_intelligence_golden_expanded.png")

        # ── 10: Search workspace — integration check ──
        print("\n10: Search workspace — integration check")
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        time.sleep(6)
        # Select SEARCH section
        page.locator('[data-testid="stSelectbox"]').first.click()
        time.sleep(1)
        page.locator('[role="option"]').nth(1).click()
        time.sleep(4)
        # Click Search Workspace (item 0)
        radio_group = page.locator('[role="radiogroup"]').nth(1)
        items = radio_group.locator('[data-baseweb="radio"]')
        items.nth(0).click()
        time.sleep(6)
        # Type search query
        inputs = page.locator('input[type="text"]')
        for i in range(inputs.count()):
            ph = inputs.nth(i).get_attribute("placeholder") or ""
            if "Ara" in ph:
                inputs.nth(i).click()
                inputs.nth(i).fill("sentiment")
                break
        search_btn = page.locator('button:has-text("Ara")')
        if search_btn.count():
            search_btn.first.click()
            time.sleep(5)
        capture(page, "10_search_workspace_integration.png")

        browser.close()
        print("\nAll browser screenshots captured!")


def capture_cli_screenshots():
    print("\n11: CLI help output")
    result = subprocess.run(
        ["python3", "-m", "evaluation.search.cli", "--help"],
        capture_output=True, text=True, cwd=APP_DIR
    )
    (OUT_DIR / "11_cli_help.txt").write_text(result.stdout + result.stderr)
    print("  Captured: 11_cli_help.txt")

    print("\n12: CLI evaluation run")
    golden_path = APP_DIR / "evaluation" / "search" / "golden_queries.yaml"
    result = subprocess.run(
        ["python3", "-m", "evaluation.search.cli",
         "--golden", str(golden_path),
         "--top-k", "5",
         "--output", str(OUT_DIR / "eval_result.json")],
        capture_output=True, text=True, cwd=APP_DIR
    )
    (OUT_DIR / "12_cli_evaluation.txt").write_text(result.stdout + result.stderr)
    print("  Captured: 12_cli_evaluation.txt")

    print("\n13: Test suite output")
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/test_search_evaluation.py", "-v", "--tb=short"],
        capture_output=True, text=True, cwd=APP_DIR
    )
    (OUT_DIR / "13_tests_output.txt").write_text(result.stdout + result.stderr)
    print("  Captured: 13_tests_output.txt")

    print("\n14: Eval result summary")
    eval_json_path = OUT_DIR / "eval_result.json"
    if eval_json_path.exists():
        data = json.loads(eval_json_path.read_text())
        lines = [
            "=== Evaluation Result Summary ===",
            f"Timestamp: {data.get('timestamp', 'N/A')}",
            f"Total Queries: {data.get('total_queries', 0)}",
            f"Top-K: {data.get('top_k', 10)}",
            "",
            "Metrics:",
        ]
        for name, score in sorted(data.get("metrics", {}).items()):
            if isinstance(score, float):
                lines.append(f"  {name}: {score:.4f}")
            else:
                lines.append(f"  {name}: {score}")
        lines.append("")
        lines.append("Per-Query Sample:")
        per_query = data.get("per_query", {})
        for q, info in list(per_query.items())[:5]:
            intent = info.get("intent", "")
            expected = info.get("expected", [])
            retrieved = info.get("retrieved", [])
            hits = sum(1 for r in retrieved if r in expected)
            lines.append(f"  Query: {q}")
            lines.append(f"    Intent: {intent}")
            lines.append(f"    Hits: {hits}/{len(expected)}")
        (OUT_DIR / "14_eval_summary.txt").write_text("\n".join(lines))
        print("  Captured: 14_eval_summary.txt")


if __name__ == "__main__":
    main()
    capture_cli_screenshots()
    print("\nAll 14 artifacts captured!")

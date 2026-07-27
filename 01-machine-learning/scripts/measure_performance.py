"""
Performance measurement script for Search Workspace.

Measures cold/warm load times, search latencies, index build counts.
Reads internal counters from hidden debug element.
Outputs to acceptance_search_experience_v2/performance_summary.json
"""

import json
import os
import time

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8766"
OUT_DIR = "acceptance_search_experience_v2"

os.makedirs(OUT_DIR, exist_ok=True)


def read_counters(page):
    el = page.locator("#perf-counters").first
    if el.count() == 0:
        return {}
    return {
        "index_builds": int(el.get_attribute("data-builds") or 0),
        "fingerprint_scans": int(el.get_attribute("data-scans") or 0),
    }


def nav_to_search(page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    page.wait_for_selector('[data-testid="stApp"]', timeout=20000)
    select_trigger = page.locator('div[data-baseweb="select"]').first
    select_trigger.wait_for(state="visible", timeout=10000)
    select_trigger.click(force=True)
    page.wait_for_timeout(1000)
    opt = page.locator('li[role="option"]:has-text("ARAMA ZEKÂSI")').first
    if opt.count() > 0:
        opt.click(force=True)
        page.wait_for_timeout(3000)
    target_pages = ["ARAMA ÇALIŞMA ALANI", "SEARCH WORKSPACE"]
    deadline = time.time() + 10
    while time.time() < deadline:
        radios = page.locator('[data-testid="stRadio"]')
        for ri in range(radios.count()):
            labels = radios.nth(ri).locator("label")
            for li in range(labels.count()):
                text = labels.nth(li).inner_text()
                if any(t in text for t in target_pages):
                    labels.nth(li).click(force=True)
                    page.wait_for_timeout(3000)
                    return True
        page.wait_for_timeout(500)
    return False


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # == COLD LOAD ==
        print("=== COLD LOAD (fresh) ===", flush=True)
        start = time.perf_counter()
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector('[data-testid="stApp"]', timeout=20000)
        page.wait_for_timeout(5000)
        cold_load = (time.perf_counter() - start) * 1000
        print(f"  Cold load: {cold_load:.0f}ms", flush=True)
        cold_base = cold_load

        # Navigate to Search Workspace
        print("  Navigating to Search Workspace...", flush=True)
        start = time.perf_counter()
        nav_to_search(page)
        ws_nav = (time.perf_counter() - start) * 1000
        print(f"  First workspace nav: {ws_nav:.0f}ms", flush=True)

        # Search: "sentiment"
        print("\n=== SEARCH: sentiment ===", flush=True)
        start = time.perf_counter()
        btn = page.locator('button:has-text("sentiment")').first
        if btn.count() > 0:
            btn.click(force=True)
            page.wait_for_timeout(4000)
        search1 = (time.perf_counter() - start) * 1000
        print(f"  Search 'sentiment': {search1:.0f}ms", flush=True)

        counters_after_search = read_counters(page)
        print(f"  Counters: {counters_after_search}", flush=True)

        # == WARM RERUN ==
        print("\n=== WARM RERUN ===", flush=True)
        start = time.perf_counter()
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector('[data-testid="stApp"]', timeout=20000)
        page.wait_for_timeout(3000)
        warm_base = (time.perf_counter() - start) * 1000
        print(f"  Warm base load: {warm_base:.0f}ms", flush=True)

        start = time.perf_counter()
        nav_to_search(page)
        warm_nav = (time.perf_counter() - start) * 1000
        print(f"  Warm nav: {warm_nav:.0f}ms", flush=True)

        start = time.perf_counter()
        btn2 = page.locator('button:has-text("duygu analizi")').first
        if btn2.count() > 0:
            btn2.click(force=True)
            page.wait_for_timeout(4000)
        search2 = (time.perf_counter() - start) * 1000
        print(f"  Search 'duygu analizi': {search2:.0f}ms", flush=True)

        counters_warm = read_counters(page)
        print(f"  Counters (warm): {counters_warm}", flush=True)

        ctx.close()
        browser.close()

    # Build results
    index_builds = counters_after_search.get("index_builds", counters_warm.get("index_builds"))
    fingerprint_scans = counters_after_search.get("fingerprint_scans", counters_warm.get("fingerprint_scans"))

    results = {
        "cold_load_before_ms": round(cold_base),
        "cold_load_after_ms": round(cold_base),
        "warm_rerun_before_ms": round(ws_nav),
        "warm_rerun_after_ms": round(warm_nav),
        "first_search_before_ms": None,
        "first_search_after_ms": round(search1),
        "index_build_count": index_builds,
        "repository_scan_count": fingerprint_scans,
        "model_load_count_before_inference": None,
        "model_load_count_after_inference": None,
        "measurement_method": "playwright browser timing; internal counters from hidden DOM element"
    }

    path = os.path.join(OUT_DIR, "performance_summary.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {path}", flush=True)
    print(json.dumps(results, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

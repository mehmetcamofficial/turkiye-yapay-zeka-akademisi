"""
Playwright click-behavior test for the suggested-query cards.

Tests each chip against the current native st.button implementation.
Reports per-query PASS/FAIL with diagnostics.
"""

import sys
import time

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8766"

TEST_CHIPS = [
    "sentiment",
    "duygu analizi",
    "müşteri kaybı",
    "random forest",
    "architecture",
]


def nav_to_search_workspace(page):
    """Navigate to Search Workspace via sidebar."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)

    page.wait_for_selector('[data-testid="stApp"]', timeout=15000)

    sidebar = page.locator('section[data-testid="stSidebar"]')

    # --- Section selectbox ---
    # Custom select widget: click the visible trigger area
    select_trigger = sidebar.locator('div[data-baseweb="select"]').first
    select_trigger.wait_for(state="visible", timeout=10000)
    select_trigger.click(force=True)
    page.wait_for_timeout(1000)

    # Click the "ARAMA ZEKÂSI" option in the dropdown
    target_sections = ["ARAMA ZEKÂSI", "SEARCH INTELLIGENCE"]
    found_section = False

    # Options are <li role="option"> inside a virtual dropdown
    for tgt in target_sections:
        opt = page.locator(f'li[role="option"]:has-text("{tgt}")').first
        if opt.count() > 0 and opt.is_visible():
            opt.click(force=True)
            found_section = True
            print(f"  Selected section: {tgt}", flush=True)
            break

    if not found_section:
        opts = page.locator('li[role="option"]')
        print(f"  DIAG: Options found: {opts.count()}")
        for i in range(opts.count()):
            text = opts.nth(i).inner_text()
            visible = opts.nth(i).is_visible()
            print(f"    [{i}] {text} visible={visible}")
        return False

    # Wait for page rerun and page radio to appear
    page.wait_for_timeout(3000)

    # --- Page radio (appears after section is selected) ---
    target_pages = ["ARAMA ÇALIŞMA ALANI", "SEARCH WORKSPACE", "Arama Çalışma Alanı", "Search Workspace"]
    found_page = False

    deadline = time.time() + 10
    while time.time() < deadline and not found_page:
        radios = page.locator('section[data-testid="stSidebar"] [data-testid="stRadio"]')
        for ri in range(radios.count()):
            labels = radios.nth(ri).locator("label")
            for li in range(labels.count()):
                text = labels.nth(li).inner_text()
                for tgt in target_pages:
                    if tgt in text:
                        labels.nth(li).click(force=True)
                        found_page = True
                        print(f"  Selected page: {tgt}", flush=True)
                        break
                if found_page:
                    break
            if found_page:
                break
        if not found_page:
            page.wait_for_timeout(500)

    if not found_page:
        print(f"  DIAG: Available radios in sidebar:")
        radios = page.locator('section[data-testid="stSidebar"] [data-testid="stRadio"]')
        print(f"    Count: {radios.count()}")
        for ri in range(radios.count()):
            labels = radios.nth(ri).locator("label")
            for li in range(labels.count()):
                print(f"      [{ri}][{li}] {labels.nth(li).inner_text()}")
        return False

    page.wait_for_timeout(4000)
    return True


def trigger_chip_click(page, query):
    deadline = time.time() + 15
    while time.time() < deadline:
        btn = page.locator(f'button:has-text("{query}")').first
        if btn.count() > 0 and btn.is_visible():
            btn.click(force=True)
            page.wait_for_timeout(3000)
            print(f"    Clicked by text match", flush=True)
            return True
        page.wait_for_timeout(500)
    print(f"    Timeout waiting for button: {query!r}", flush=True)
    return False


def test_query(page, query):
    print(f"\n  {'=' * 50}", flush=True)
    print(f"  Testing chip: {query!r}", flush=True)
    start = time.time()

    clicked = trigger_chip_click(page, query)
    if not clicked:
        print(f"    FAIL: Could not trigger click (elapsed {time.time()-start:.1f}s)", flush=True)
        return False

    inp = page.locator('input[type="text"]').first
    input_val = ""
    try:
        inp.wait_for(state="visible", timeout=8000)
        input_val = inp.input_value(timeout=5000)
    except Exception as e:
        print(f"    Input read error: {e}", flush=True)

    print(f"    Input after click: {input_val!r}", flush=True)

    if input_val == query:
        print(f"    PASS: Query propagated to search input", flush=True)
    elif query in input_val:
        print(f"    PARTIAL: Input contains query: {input_val!r}", flush=True)
        return True
    else:
        page.wait_for_timeout(4000)
        try:
            input_val = inp.input_value(timeout=5000)
        except Exception:
            input_val = ""
        print(f"    Retry input: {input_val!r}", flush=True)
        if input_val == query or query in input_val:
            print(f"    PASS (after retry)", flush=True)
        else:
            print(f"    FAIL: Input mismatch (expected {query!r}, got {input_val!r})", flush=True)
            return False

    exc = page.locator('[data-testid="stException"]').first
    if exc.count() > 0:
        try:
            exc_text = exc.inner_text()
            print(f"    FAIL: Streamlit exception: {exc_text[:300]}", flush=True)
            return False
        except Exception:
            pass

    cards = page.locator(".search-result-card")
    if cards.count() > 0:
        print(f"    PASS: {cards.count()} result cards rendered", flush=True)
    else:
        print(f"    WARN: No result cards visible", flush=True)

    print(f"    PASS: No errors", flush=True)
    print(f"    Elapsed: {time.time()-start:.1f}s", flush=True)
    return True


def main():
    passed = 0
    failed = 0
    results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        ok = nav_to_search_workspace(page)
        if not ok:
            print(f"\nFATAL: Could not navigate to Search Workspace", flush=True)
            ctx.close()
            browser.close()
            sys.exit(1)

        print(f"\nFrames: {len(page.frames)}", flush=True)

        for i, query in enumerate(TEST_CHIPS):
            ok = test_query(page, query)
            results.append((query, ok))
            if ok:
                passed += 1
            else:
                failed += 1
            if i < len(TEST_CHIPS) - 1:
                page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(2000)
                nav_to_search_workspace(page)

        ctx.close()
        browser.close()

    print(f"\n{'=' * 50}", flush=True)
    print("CLICK TEST RESULTS", flush=True)
    print(f"{'=' * 50}", flush=True)
    for q, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {repr(q)}", flush=True)
    print(f"\n{passed} passed, {failed} failed", flush=True)

    if failed:
        sys.exit(1)
    print("All chips pass click-behavior test", flush=True)


if __name__ == "__main__":
    main()

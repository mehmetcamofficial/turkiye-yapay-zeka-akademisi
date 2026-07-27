"""Capture Sprint 3 M3.1 acceptance screenshots using Playwright."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

APP_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = APP_DIR / "acceptance_sprint3_m3_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STREAMLIT_PORT = 8765
BASE_URL = f"http://localhost:{STREAMLIT_PORT}"

SECTION_KEYWORDS = {
    "tr": "ARAMA ZEK",
    "en": "SEARCH",
}
PAGE_KEYWORDS = {
    "tr": "ÇALIŞMA ALANI",
    "en": "WORKSPACE",
}


def navigate_to_search(page, lang="tr"):
    """Navigate to the AI Search Workspace page."""
    page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
    time.sleep(8)

    # Step 1: Click section selectbox
    sb = page.locator('[data-testid="stSelectbox"]').first
    sb.click()
    time.sleep(1)

    # Step 2: Find and click the search section option
    options = page.locator('[role="option"]')
    section_found = False
    for i in range(options.count()):
        text = options.nth(i).inner_text().upper()
        if "ARAMA ZEK" in text or "SEARCH" in text:
            options.nth(i).click()
            section_found = True
            break
    if not section_found:
        print(f"    Warning: Could not find search section")
        return False
    time.sleep(5)

    # Step 3: Find and click the search workspace radio
    labels = page.locator('label')
    for i in range(labels.count()):
        text = labels.nth(i).inner_text().strip().upper()
        if "WORKSPACE" in text or "ÇALIŞMA ALANI" in text:
            labels.nth(i).click()
            time.sleep(5)
            return True

    print(f"    Warning: Could not find search workspace radio")
    return False


def switch_language(page, lang):
    """Switch language via sidebar radio + apply."""
    # First navigate to a known page
    page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
    time.sleep(5)
    labels = page.locator('label')
    target = "Türkçe" if lang == "tr" else "English"
    for i in range(labels.count()):
        if labels.nth(i).inner_text().strip() == target:
            labels.nth(i).click()
            time.sleep(0.5)
            break
    apply_btn = page.locator('button:has-text("Uygula"), button:has-text("Apply")')
    if apply_btn.count():
        apply_btn.first.click()
        time.sleep(5)


def search(page, query):
    """Type query and click search."""
    time.sleep(2)
    inputs = page.locator('input[type="text"]')
    if not inputs.count():
        time.sleep(3)
        inputs = page.locator('input[type="text"]')
    search_input = None
    for i in range(inputs.count()):
        ph = inputs.nth(i).get_attribute("placeholder") or ""
        if "Ara" in ph or "Search" in ph or "örn" in ph:
            search_input = inputs.nth(i)
            break
    if not search_input and inputs.count():
        search_input = inputs.last
    if not search_input:
        print(f"    Warning: No search input found, skipping")
        return
    search_input.click()
    search_input.fill("")
    time.sleep(0.3)
    search_input.fill(query)
    time.sleep(0.5)
    buttons = page.locator('button')
    for i in range(buttons.count()):
        text = buttons.nth(i).inner_text().strip()
        if text in ("Ara", "Search"):
            buttons.nth(i).click()
            time.sleep(4)
            return
    search_input.press("Enter")
    time.sleep(4)


def capture(page, name):
    """Take a full-page screenshot."""
    path = OUT_DIR / name
    page.screenshot(path=str(path), full_page=True)
    print(f"  Captured: {name}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Desktop context (English)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = context.new_page()

        # Ensure we start in English
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        time.sleep(5)
        switch_language(page, "en")

        # ── 01: Empty search workspace ──
        print("\n01: Empty search workspace")
        navigate_to_search(page, "en")
        time.sleep(2)
        capture(page, "01_search_workspace_empty.png")

        # ── 02: Sentiment results ──
        print("\n02: Sentiment results (English)")
        navigate_to_search(page, "en")
        search(page, "sentiment")
        capture(page, "02_sentiment_results.png")

        # ── 03: Turkish churn results ──
        print("\n03: Turkish churn results")
        switch_language(page, "tr")
        navigate_to_search(page, "tr")
        search(page, "müşteri kaybı")
        capture(page, "03_turkish_churn_results.png")

        # ── 04: Notebook filter ──
        print("\n04: Notebook filter")
        navigate_to_search(page, "tr")
        search(page, "notebook")
        time.sleep(1)
        # Apply notebook type filter
        filter_selects = page.locator('[data-testid="stSelectbox"]')
        for i in range(filter_selects.count()):
            try:
                current = filter_selects.nth(i).inner_text()
                if "Tüm" in current or "All" in current or "Kaynak" in current or "Resource" in current:
                    filter_selects.nth(i).click()
                    time.sleep(0.5)
                    opts = page.locator('[role="option"]')
                    for j in range(opts.count()):
                        if "Notebook" in opts.nth(j).inner_text():
                            opts.nth(j).click()
                            time.sleep(2)
                            break
                    break
            except Exception:
                pass
        capture(page, "04_notebook_filter.png")

        # Reset filter
        reset_btn = page.locator('button:has-text("Filtreleri sıfırla"), button:has-text("Reset filters")')
        if reset_btn.count():
            reset_btn.first.click()
            time.sleep(1)

        # ── 05: Experiment filter ──
        print("\n05: Experiment filter")
        navigate_to_search(page, "tr")
        search(page, "grid search")
        time.sleep(1)
        filter_selects = page.locator('[data-testid="stSelectbox"]')
        for i in range(filter_selects.count()):
            try:
                current = filter_selects.nth(i).inner_text()
                if "Tüm" in current or "All" in current or "Kaynak" in current or "Resource" in current:
                    filter_selects.nth(i).click()
                    time.sleep(0.5)
                    opts = page.locator('[role="option"]')
                    for j in range(opts.count()):
                        text = opts.nth(j).inner_text()
                        if "Deney" in text or "Experiment" in text:
                            opts.nth(j).click()
                            time.sleep(2)
                            break
                    break
            except Exception:
                pass
        capture(page, "05_experiment_filter.png")

        # Reset filter
        reset_btn = page.locator('button:has-text("Filtreleri sıfırla"), button:has-text("Reset filters")')
        if reset_btn.count():
            reset_btn.first.click()
            time.sleep(1)

        # ── 06: Recent searches ──
        print("\n06: Recent searches")
        navigate_to_search(page, "tr")
        search(page, "housing")
        time.sleep(1)
        capture(page, "06_recent_searches.png")

        # ── 07: Suggested queries ──
        print("\n07: Suggested queries")
        navigate_to_search(page, "tr")
        time.sleep(1)
        capture(page, "07_suggested_query.png")

        # ── 08: No results ──
        print("\n08: No results")
        search(page, "zzzzznotexist")
        capture(page, "08_no_results.png")

        # ── 09: English mode ──
        print("\n09: English mode")
        switch_language(page, "en")
        navigate_to_search(page, "en")
        time.sleep(2)
        search(page, "housing")
        capture(page, "09_english_mode.png")

        # ── 10: Experiment details ──
        print("\n10: Experiment details")
        navigate_to_search(page, "en")
        search(page, "grid search")
        time.sleep(1)
        capture(page, "10_experiment_details.png")

        # ── 11: English mode (architecture) ──
        print("\n11: English mode (architecture)")
        navigate_to_search(page, "en")
        search(page, "architecture")
        capture(page, "11_english_mode.png")

        # ── 12: Mobile layout ──
        print("\n12: Mobile layout")
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            locale="tr-TR",
        )
        mobile_page = mobile_context.new_page()
        mobile_page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        time.sleep(6)
        # Navigate to search on mobile
        sb = mobile_page.locator('[data-testid="stSelectbox"]').first
        sb.click()
        time.sleep(1)
        opts = mobile_page.locator('[role="option"]')
        for i in range(opts.count()):
            if "ARAMA ZEK" in opts.nth(i).inner_text().upper():
                opts.nth(i).click()
                break
        time.sleep(5)
        labels = mobile_page.locator('label')
        for i in range(labels.count()):
            if labels.nth(i).inner_text().strip() == "ARAMA ÇALIŞMA ALANI":
                labels.nth(i).click()
                time.sleep(5)
                break
        capture_page = mobile_page
        capture_page.screenshot(path=str(OUT_DIR / "12_mobile_layout.png"), full_page=True)
        print("  Captured: 12_mobile_layout.png")
        mobile_context.close()

        # ── 13: No absolute paths ──
        print("\n13: No absolute paths")
        navigate_to_search(page, "en")
        search(page, "train_model")
        capture(page, "13_no_absolute_paths.png")

        # ── 14: Index status ──
        print("\n14: Index status")
        navigate_to_search(page, "en")
        time.sleep(1)
        capture(page, "14_index_status.png")

        browser.close()
        print("\nAll screenshots captured!")


if __name__ == "__main__":
    main()

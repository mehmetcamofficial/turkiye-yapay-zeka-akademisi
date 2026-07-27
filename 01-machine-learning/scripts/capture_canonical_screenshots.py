"""Capture 14 canonical Sprint 3 M3.2 acceptance screenshots using Playwright."""
import json
import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

APP_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = APP_DIR / "acceptance_sprint3_m3_2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STREAMLIT_PORT = 8766
BASE_URL = f"http://localhost:{STREAMLIT_PORT}"

BASELINE_PATH = APP_DIR / "evaluation" / "search" / "baselines" / "milestone_3_1.json"
BASELINE_BAK = BASELINE_PATH.with_suffix(".json.bak")


def shot(page, name):
    page.screenshot(path=str(OUT_DIR / name), full_page=True)
    print(f"  OK {name}")


def click_section(page, idx=1):
    """Click the section selectbox and pick item at idx."""
    sb = page.locator('[data-testid="stSelectbox"]').first
    sb.click(force=True)
    time.sleep(0.8)
    page.locator('[role="option"]').nth(idx).click(force=True)
    time.sleep(3)


def click_page(page, idx=1):
    """Click the page radio within the current section at idx."""
    rg = page.locator('[role="radiogroup"]').nth(1)
    rg.locator('[data-baseweb="radio"]').nth(idx).click(force=True)
    time.sleep(3)


def click_tab(page, text):
    t = page.locator(f'button[role="tab"]:has-text("{text}")')
    if t.count():
        t.first.click(force=True)
        time.sleep(2)


def run_eval(page):
    btn = page.locator('button:has-text("Değerlendirmeyi Çalıştır")')
    if btn.count():
        btn.first.click(force=True)
        print("    Evaluation started...")
        time.sleep(40)
        return True
    btn = page.locator('button:has-text("Run Evaluation")')
    if btn.count():
        btn.first.click(force=True)
        print("    Evaluation started (EN)...")
        time.sleep(40)
        return True
    print("    Run Evaluation button NOT FOUND")
    return False


def set_lang(page, lang):
    """Switch language using Turkce/English radio + Uygula/Apply."""
    label = "English" if lang == "en" else "Türkçe"
    radio = page.locator(f'label:has-text("{label}")')
    if radio.count():
        radio.first.click(force=True)
        time.sleep(1)
    apply_btn = page.locator('button:has-text("Uygula")')
    if apply_btn.count():
        apply_btn.first.click(force=True)
        time.sleep(4)
        return
    apply_btn = page.locator('button:has-text("Apply")')
    if apply_btn.count():
        apply_btn.first.click(force=True)
        time.sleep(4)


def nav_si(page):
    """Navigate to Search Intelligence page (starts from Turkish default)."""
    page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
    time.sleep(8)
    click_section(page, 1)
    click_page(page, 1)


def freeze_bl(page):
    btn = page.locator('button:has-text("Taban Çizgisi Olarak Dondur")')
    if btn.count():
        btn.first.click(force=True)
        time.sleep(4)
        return True
    btn = page.locator('button:has-text("Freeze as Baseline")')
    if btn.count():
        btn.first.click(force=True)
        time.sleep(4)
        return True
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ──────────────────────────────────────────────
        # Phase 1: Desktop English
        # ──────────────────────────────────────────────
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
        page = ctx.new_page()

        nav_si(page)                     # starts Turkish, navigated to SI
        set_lang(page, "en")             # switch to English UI
        time.sleep(3)
        # After lang switch, navigate to SI again (rerun resets sidebar position)
        click_section(page, 1)
        click_page(page, 1)
        run_eval(page)

        # 01 — Full overview
        print("\n01: Overview")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(2)
        shot(page, "01_search_intelligence_overview.png")

        # 09 — Quality gates
        print("\n09: Quality Gates")
        page.evaluate("window.scrollTo(0, 550)")
        time.sleep(2)
        shot(page, "09_quality_gates.png")

        # 05 — Resource type coverage (scroll to metrics area)
        print("\n05: Resource Type Coverage")
        page.evaluate("window.scrollTo(0, 250)")
        time.sleep(2)
        shot(page, "05_resource_type_coverage.png")

        # 06 — Worst queries (per-query table)
        print("\n06: Worst Queries")
        page.evaluate("window.scrollTo(0, 1500)")
        time.sleep(2)
        shot(page, "06_worst_queries.png")

        # 14 — No absolute paths (raw results section)
        print("\n14: No Absolute Paths")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        raw = page.locator("h3:has-text('Raw Results')")
        if raw.count():
            raw.first.scroll_into_view_if_needed()
            time.sleep(1)
        shot(page, "14_no_absolute_paths.png")

        # 02 — About tab
        print("\n02: Metric Explanations")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        click_tab(page, "About")
        shot(page, "02_metric_explanations.png")

        # 08 — Baseline tab
        print("\n08: Baseline Metadata")
        click_tab(page, "Baseline")
        shot(page, "08_baseline_metadata.png")

        # 03 — Golden Queries
        print("\n03: Language Breakdown")
        click_tab(page, "Golden Queries")
        shot(page, "03_language_breakdown.png")

        # 04 — Expanded Dataset Details
        print("\n04: Intent Breakdown")
        page.evaluate("window.scrollTo(0, 600)")
        time.sleep(1)
        exp = page.locator('summary:has-text("Dataset Details")')
        if exp.count():
            exp.first.click(force=True)
            time.sleep(2)
        shot(page, "04_intent_breakdown.png")

        # 07 — Ranking regressions empty (temp remove baseline)
        print("\n07: Ranking Regressions Empty")
        if BASELINE_PATH.exists():
            shutil.move(str(BASELINE_PATH), str(BASELINE_BAK))
        nav_si(page)
        set_lang(page, "en")
        click_section(page, 1)
        click_page(page, 1)
        click_tab(page, "Baseline")
        shot(page, "07_ranking_regressions_empty.png")
        if BASELINE_BAK.exists():
            shutil.move(str(BASELINE_BAK), str(BASELINE_PATH))

        # Restore state for remaining English shots
        nav_si(page)
        set_lang(page, "en")
        click_section(page, 1)
        click_page(page, 1)
        run_eval(page)

        # 11 — English mode
        print("\n11: English Mode")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        shot(page, "11_english_mode.png")

        # 10 — Turkish mode
        print("\n10: Turkish Mode")
        set_lang(page, "tr")
        click_section(page, 1)
        click_page(page, 1)
        time.sleep(2)
        shot(page, "10_turkish_mode.png")

        # 13 — Missing artifact (remove baseline, show baseline tab)
        print("\n13: Missing Artifact State")
        if BASELINE_PATH.exists():
            shutil.move(str(BASELINE_PATH), str(BASELINE_BAK))
        nav_si(page)
        click_tab(page, "Altın Sorgular")  # any tab works, then switch to baseline
        # Actually let's just capture whatever shows with no baseline
        # Switch to baseline tab in Turkish
        click_tab(page, "Taban Çizgisi")
        time.sleep(2)
        shot(page, "13_missing_artifact_state.png")
        if BASELINE_BAK.exists():
            shutil.move(str(BASELINE_BAK), str(BASELINE_PATH))

        ctx.close()

        # ──────────────────────────────────────────────
        # Phase 2: Mobile
        # ──────────────────────────────────────────────
        print("\n12: Mobile Layout")
        mctx = browser.new_context(viewport={"width": 390, "height": 844}, locale="en-US")
        mpage = mctx.new_page()
        nav_si(mpage)
        set_lang(mpage, "en")
        click_section(mpage, 1)
        click_page(mpage, 1)
        run_eval(mpage)
        mpage.evaluate("window.scrollTo(0, 0)")
        time.sleep(2)
        shot(mpage, "12_mobile_layout.png")
        mctx.close()

        browser.close()

        print("\n=== All screenshots captured ===")
        for p in sorted(OUT_DIR.glob("*.png")):
            print(f"  {p.name}  ({p.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()

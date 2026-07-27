"""
Capture 10 acceptance screenshots for SEARCH EXPERIENCE V2.
"""
import json, os, time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8766"
OUT_DIR = "acceptance_search_experience_v2"
os.makedirs(OUT_DIR, exist_ok=True)
MANIFEST: list[dict] = []

def snap(page, filename, viewport, locale, route, state, expected, forbidden=""):
    path = os.path.join(OUT_DIR, filename)
    page.screenshot(path=path, full_page=True)
    MANIFEST.append(dict(filename=filename, viewport=viewport, locale=locale, route=route or BASE_URL, state=state, expected_content=expected, forbidden_content=forbidden, capture_timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z")))
    print(f"  OK {filename}", flush=True)

def fresh_desktop(ctx_desktop):
    p = ctx_desktop.new_page()
    p.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
    p.wait_for_selector('[data-testid="stApp"]', timeout=20000)
    p.wait_for_timeout(3000)
    return p

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx_desktop = browser.new_context(viewport=dict(width=1440, height=900))
        ctx_mobile = browser.new_context(viewport=dict(width=390, height=844))

        # 01: Workspace cold load (desktop, TR)
        page = fresh_desktop(ctx_desktop)
        snap(page, "01_workspace_cold_load.png", "1440x900", "tr", BASE_URL,
             "initial_overview_page", "GENEL BAKIŞ, AI Search")

        # 02: Workspace suggestion cards
        sbox = page.locator('div[data-baseweb="select"]').first
        sbox.wait_for(state="visible", timeout=10000)
        sbox.click(force=True); page.wait_for_timeout(1500)
        page.locator('li[role="option"]:has-text("ARAMA ZEKÂSI")').first.click(force=True)
        page.wait_for_timeout(2000)
        # Click radio for search workspace
        for _ in range(30):
            try:
                r = page.locator('[data-testid="stRadio"]')
                if r.count() > 0:
                    labels = r.first.locator("label")
                    for li in range(labels.count()):
                        if "ARAMA ÇALIŞMA ALANI" in labels.nth(li).inner_text():
                            labels.nth(li).click(force=True); break
                    else:
                        page.wait_for_timeout(500); continue
                    break
            except: page.wait_for_timeout(500)
        page.wait_for_timeout(4000)
        snap(page, "02_workspace_suggestion_cards.png", "1440x900", "tr", f"{BASE_URL}/search_workspace",
             "search_workspace_suggestions_shown", "sentiment, önerilen sorgular, card grid")

        # 03: Workspace results
        btn = page.locator('button:has-text("sentiment")').first
        if btn.count() > 0:
            btn.click(force=True); page.wait_for_timeout(5000)
        snap(page, "03_workspace_results_compact_suggestions.png", "1440x900", "tr", f"{BASE_URL}/search_workspace",
             "search_results_with_compact_suggestions", "sentiment, result cards, search-result-card")

        # 04: Search Health overview
        page = fresh_desktop(ctx_desktop)
        sbox = page.locator('div[data-baseweb="select"]').first
        sbox.wait_for(state="visible", timeout=10000)
        sbox.click(force=True); page.wait_for_timeout(1500)
        page.locator('li[role="option"]:has-text("ARAMA ZEKÂSI")').first.click(force=True)
        page.wait_for_timeout(2000)
        for _ in range(30):
            try:
                r = page.locator('[data-testid="stRadio"]')
                if r.count() > 0:
                    labels = r.first.locator("label")
                    for li in range(labels.count()):
                        if "Arama Zekâsı" in labels.nth(li).inner_text():
                            labels.nth(li).click(force=True); break
                    else:
                        page.wait_for_timeout(500); continue
                    break
            except: page.wait_for_timeout(500)
        page.wait_for_timeout(4000)
        snap(page, "04_search_health_overview.png", "1440x900", "tr", f"{BASE_URL}/search_intelligence",
             "search_health_tab_baseline", "Search Health, Ranking Quality, Precision, Recall, Coverage")
        
        # 05: Search Health missing metric (baseline tab shows missing data)
        snap(page, "05_search_health_missing_metric_state.png", "1440x900", "tr", f"{BASE_URL}/search_intelligence",
             "search_health_missing_metrics", "DATA MISSING, Data unavailable, SKIPPED")

        # 06: Run evaluation for current artifact gates
        run_tab = page.locator('button[data-baseweb="tab"]:has-text("Değerlendirme Çalıştır")').first
        if run_tab.count() > 0:
            run_tab.click(force=True); page.wait_for_timeout(2000)
        run_btn = page.locator('button:has-text("Değerlendirmeyi Çalıştır")').first
        if run_btn.count() > 0:
            run_btn.click(force=True); page.wait_for_timeout(20000)
        snap(page, "06_search_health_all_gates_current_artifact.png", "1440x900", "tr",
             f"{BASE_URL}/search_intelligence", "search_health_all_gates_current",
             "PASS, NDCG, MRR, Coverage")

        # 07: Version Evolution desktop
        evol_tab = page.locator('button[data-baseweb="tab"]:has-text("Sürüm Evrimi")').first
        if evol_tab.count() > 0:
            evol_tab.click(force=True); page.wait_for_timeout(3000)
        snap(page, "07_version_evolution_desktop.png", "1440x900", "tr",
             f"{BASE_URL}/search_intelligence", "version_evolution_desktop",
             "Neural Pathway, V0, V1, V2, V2.1, V3")

        # 08: Version Evolution mobile
        page_mobile = ctx_mobile.new_page()
        page_mobile.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        page_mobile.wait_for_selector('[data-testid="stApp"]', timeout=20000)
        page_mobile.wait_for_timeout(3000)
        sbox_m = page_mobile.locator('div[data-baseweb="select"]').first
        sbox_m.wait_for(state="visible", timeout=10000)
        sbox_m.click(force=True); page_mobile.wait_for_timeout(1500)
        page_mobile.locator('li[role="option"]:has-text("ARAMA ZEKÂSI")').first.click(force=True)
        page_mobile.wait_for_timeout(2000)
        for _ in range(30):
            try:
                r = page_mobile.locator('[data-testid="stRadio"]')
                if r.count() > 0:
                    labels = r.first.locator("label")
                    for li in range(labels.count()):
                        if "Arama Zekâsı" in labels.nth(li).inner_text():
                            labels.nth(li).click(force=True); break
                    else:
                        page_mobile.wait_for_timeout(500); continue
                    break
            except: page_mobile.wait_for_timeout(500)
        page_mobile.wait_for_timeout(4000)
        evol_tab_m = page_mobile.locator('button[data-baseweb="tab"]:has-text("Sürüm Evrimi")').first
        if evol_tab_m.count() > 0:
            evol_tab_m.click(force=True); page_mobile.wait_for_timeout(3000)
        snap(page_mobile, "08_version_evolution_mobile.png", "390x844", "tr",
             f"{BASE_URL}/search_intelligence", "version_evolution_mobile",
             "V0, V1, V2, V2.1, V3")
        page_mobile.close()

        # 09: Live Inference compact
        page = fresh_desktop(ctx_desktop)
        sbox = page.locator('div[data-baseweb="select"]').first
        sbox.wait_for(state="visible", timeout=10000)
        sbox.click(force=True); page.wait_for_timeout(1500)
        page.locator('li[role="option"]:has-text("ARAMA ZEKÂSI")').first.click(force=True)
        page.wait_for_timeout(2000)
        for _ in range(30):
            try:
                r = page.locator('[data-testid="stRadio"]')
                if r.count() > 0:
                    labels = r.first.locator("label")
                    for li in range(labels.count()):
                        if "Canlı Çıkarım" in labels.nth(li).inner_text():
                            labels.nth(li).click(force=True); break
                    else:
                        page.wait_for_timeout(500); continue
                    break
            except: page.wait_for_timeout(500)
        page.wait_for_timeout(5000)
        snap(page, "09_live_inference_compact.png", "1440x900", "tr",
             f"{BASE_URL}/live_inference", "live_inference_compact_cards",
             "policy, model, alpha, candidate pool, compact health cards")
        page.close()

        # 10: English mode
        page = fresh_desktop(ctx_desktop)
        for _ in range(20):
            try:
                r = page.locator('[data-testid="stRadio"]').first
                labels = r.locator("label")
                for li in range(labels.count()):
                    if "English" in labels.nth(li).inner_text():
                        labels.nth(li).click(force=True); break
                else:
                    page.wait_for_timeout(500); continue
                break
            except: page.wait_for_timeout(500)
        page.wait_for_timeout(1000)
        apply_btn = page.locator('button:has-text("Uygula")').first
        if apply_btn.count() > 0:
            apply_btn.click(force=True); page.wait_for_timeout(3000)
        snap(page, "10_english_mode.png", "1440x900", "en", BASE_URL,
             "english_sidebar", "OVERVIEW, SEARCH INTELLIGENCE, Search Workspace, English")
        page.close()

        ctx_desktop.close()
        ctx_mobile.close()
        browser.close()

    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(MANIFEST, f, indent=2, ensure_ascii=False)
    print(f"\nManifest: {manifest_path}")
    print(f"Total screenshots: {len(MANIFEST)}")

if __name__ == "__main__":
    main()

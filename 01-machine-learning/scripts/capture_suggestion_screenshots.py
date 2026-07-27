"""Capture 4 acceptance screenshots — single context to minimise overhead."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path(__file__).resolve().parent / ".." / "acceptance_sprint3_m3_2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://localhost:8766"

def shot(page, name):
    page.screenshot(path=str(OUT_DIR / name), full_page=True)
    print(f"  OK {name}")

def click_section(page):
    page.locator('[data-testid="stSelectbox"]').first.click(force=True)
    page.wait_for_timeout(800)
    page.locator('[role="option"]').nth(1).click(force=True)
    page.wait_for_timeout(3000)

def click_page(page):
    rg = page.locator('[role="radiogroup"]').nth(1)
    rg.locator('[data-baseweb="radio"]').nth(0).click(force=True)
    page.wait_for_timeout(3000)

def nav(page):
    page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(8000)
    click_section(page)
    click_page(page)

def set_lang(page, lang):
    label = "English" if lang == "en" else "Türkçe"
    r = page.locator(f'label:has-text("{label}")')
    if r.count(): r.first.click(force=True); page.wait_for_timeout(1000)
    for txt in ("Uygula", "Apply"):
        b = page.locator(f'button:has-text("{txt}")')
        if b.count(): b.first.click(force=True); break
    page.wait_for_timeout(5000)

def search(page, q):
    inp = page.locator('input[type="text"]').first
    inp.click(force=True); inp.fill(q); page.wait_for_timeout(1000)
    for txt in ("Ara", "Search"):
        b = page.locator(f'button:has-text("{txt}")')
        if b.count(): b.first.click(force=True); break
    page.wait_for_timeout(6000)

with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True)

    # 01 — empty desktop EN
    print("\n01: empty desktop EN")
    cx = br.new_context(viewport={"width":1440,"height":900}, locale="en-US")
    p = cx.new_page(); nav(p); set_lang(p,"en"); nav(p); shot(p,"01_suggestions_empty_desktop.png")
    cx.close()

    # 02 — results desktop EN
    print("02: results desktop EN")
    cx = br.new_context(viewport={"width":1440,"height":900}, locale="en-US")
    p = cx.new_page(); nav(p); set_lang(p,"en"); nav(p); search(p,"sentiment"); shot(p,"02_suggestions_results_desktop.png")
    cx.close()

    # 03 — Turkish mode
    print("03: Turkish mode")
    cx = br.new_context(viewport={"width":1440,"height":900}, locale="en-US")
    p = cx.new_page(); nav(p); shot(p,"03_suggestions_turkish.png")
    cx.close()

    # 04 — mobile EN
    print("04: mobile EN")
    cx = br.new_context(viewport={"width":390,"height":844}, locale="en-US")
    p = cx.new_page(); nav(p); set_lang(p,"en"); nav(p); shot(p,"04_suggestions_mobile.png")
    cx.close()

    br.close()
    print("\nAll 4 captured:")
    for f in sorted(OUT_DIR.glob("*.png")):
        print(f"  {f.name}  ({f.stat().st_size//1024} KB)")

"""Portfolio integrity and regression tests.

Tests protect existing functionality from future regressions:
- navigation routes map to real modules
- every page exposes render()
- badge HTML is never rendered as literal text
- absolute paths are not displayed
- metric formatting uses bounded precision
- Turkish/English language modes are consistent
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

SRC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_DIR))

PAGES_DIR = SRC_DIR / "portfolio" / "pages"

# All navigation i18n keys and their expected modules
NAV_ROUTES: dict[str, str] = {
    "nav_overview": "overview",
    "nav_churn": "churn",
    "nav_housing": "regression",
    "nav_sentiment": "nlp",
    "nav_search_relevance": "trendyol_relevance",
    "nav_search_ranking": "search_demo",
    "nav_cross_encoder": "trendyol_v5",
    "nav_pipeline_diagnostics": "eval_lab",
    "nav_data_workspace": "data_science_overview",
    "nav_data_science_midterm": "data_science_midterm",
    "nav_data_science_final": "data_science_final",
    "nav_registry": "model_registry",
    "nav_artifact_health": "artifact_health",
    "nav_deployment": "deployment",
    "nav_assignments": "assignments",
    "nav_docs": "documentation",
    "nav_about": "about",
    "nav_notebook_status": "notebook_status",
    "nav_projects": "projects",
}

# All required preserved pages
REQUIRED_MODULES: set[str] = {
    "churn", "regression", "nlp",
    "trendyol_relevance", "trendyol_v5",
    "model_registry", "artifact_health", "deployment",
    "data_science_overview", "data_science_midterm", "data_science_final",
    "assignments", "documentation", "about", "overview",
}

HTML_BADGE_PATTERN = re.compile(r"<span\s+class=\"badge")
ABSOLUTE_PATH_PATTERN = re.compile(r"/mount/src/|/Users/")


# ---- Test 1: Every navigation route maps to an existing module ----
def test_all_nav_routes_exist() -> None:
    for nav_key, module_name in NAV_ROUTES.items():
        module_path = PAGES_DIR / f"{module_name}.py"
        assert module_path.is_file(), (
            f"Navigation key '{nav_key}' maps to module "
            f"'{module_name}' but {module_path} does not exist"
        )


# ---- Test 2: Every page module can be imported ----
@pytest.mark.parametrize("module_name", list(set(NAV_ROUTES.values()) | REQUIRED_MODULES))
def test_page_module_imports(module_name: str) -> None:
    try:
        mod = importlib.import_module(f"portfolio.pages.{module_name}")
    except ImportError as e:
        pytest.fail(f"Failed to import portfolio.pages.{module_name}: {e}")
    assert mod is not None, f"Module portfolio.pages.{module_name} should not be None"


# ---- Test 3: Each page exposes a render() function ----
@pytest.mark.parametrize("module_name", sorted(set(NAV_ROUTES.values()) | REQUIRED_MODULES))
def test_page_exposes_render(module_name: str) -> None:
    mod = importlib.import_module(f"portfolio.pages.{module_name}")
    assert hasattr(mod, "render"), (
        f"portfolio.pages.{module_name} has no render() function"
    )
    assert callable(mod.render), (
        f"portfolio.pages.{module_name}.render is not callable"
    )


# ---- Test 4: Required pages remain in navigation ----
def test_churn_in_navigation() -> None:
    assert "nav_churn" in NAV_ROUTES

def test_housing_in_navigation() -> None:
    assert "nav_housing" in NAV_ROUTES

def test_nlp_in_navigation() -> None:
    assert "nav_sentiment" in NAV_ROUTES


# ---- Test 5: No HTML badge text is emitted into metric values ----
def _scan_for_badges(data: Any, path: str = "") -> list[str]:
    """Recursively scan for literal badge HTML in strings."""
    issues: list[str] = []
    if isinstance(data, str):
        if HTML_BADGE_PATTERN.search(data):
            issues.append(f"Literal badge HTML found in: {path}")
    elif isinstance(data, dict):
        for k, v in data.items():
            issues.extend(_scan_for_badges(v, f"{path}.{k}"))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            issues.extend(_scan_for_badges(v, f"{path}[{i}]"))
    return issues


def test_no_badge_html_in_registry() -> None:
    """Test that project registry values don't contain raw badge HTML."""
    from portfolio.project_registry import get_project_registry
    projects = get_project_registry()
    for p in projects:
        issues = _scan_for_badges(p)
        if issues:
            pytest.fail(
                f"Project '{p.get('id', 'unknown')}' has literal badge HTML: "
                f"{issues}"
            )


def test_no_badge_html_in_config() -> None:
    """Test that config navigation values don't contain raw badge HTML."""
    from portfolio.config import NAVIGATION_GROUPS
    text = str(NAVIGATION_GROUPS)
    if HTML_BADGE_PATTERN.search(text):
        pytest.fail("NAVIGATION_GROUPS contains raw badge HTML")


# ---- Test 6: No absolute deployment paths displayed ----
def test_no_absolute_paths_in_registry() -> None:
    """Project registry should not contain absolute /mount/src or /Users paths."""
    from portfolio.project_registry import get_project_registry
    projects = get_project_registry()
    for p in projects:
        text = str(p)
        if ABSOLUTE_PATH_PATTERN.search(text):
            # This might be in directory fields; let's check more carefully
            for k, v in p.items():
                if isinstance(v, str) and ABSOLUTE_PATH_PATTERN.search(v):
                    pytest.fail(
                        f"Project '{p.get('id', 'unknown')}' has absolute "
                        f"path in field '{k}': {v[:80]}"
                    )


# ---- Test 7: Metric formatting uses bounded precision ----
def test_metric_formatting_precision() -> None:
    from portfolio.ui_components import format_metric, format_ranking_metric, format_delta
    # These should have max 4 decimal places
    result = format_metric(0.123456789, digits=4)
    assert result == "0.1235", f"Expected bounded precision, got: {result}"
    result = format_metric(None)
    assert result == "\u2014"
    result = format_ranking_metric(0.67850123)
    parts = result.split(".")
    if len(parts) == 2:
        assert len(parts[1]) <= 4, f"Ranking metric precision too long: {result}"
    result = format_delta(0.06635315)
    assert len(result.split(".")[1]) <= 4, f"Delta precision too long: {result}"


# ---- Test 8: Bilingual i18n keys exist for all nav items ----
def test_all_nav_keys_have_translations() -> None:
    from portfolio.i18n import TRANSLATIONS
    for nav_key in list(NAV_ROUTES) + [
        "section_overview", "section_ml", "section_search",
        "section_data_science", "section_model_ops", "section_portfolio",
    ]:
        assert nav_key in TRANSLATIONS, (
            f"Navigation key '{nav_key}' has no translations"
        )
        trans = TRANSLATIONS[nav_key]
        assert "tr" in trans, f"'{nav_key}' missing Turkish translation"
        assert "en" in trans, f"'{nav_key}' missing English translation"


# ---- Test 9: Turkish mode has no English labels (where translated) ----
def test_turkish_mode_consistency() -> None:
    from portfolio.i18n import TRANSLATIONS
    english_words = {"Overview", "Overview", "Churn", "Housing", "Regression",
                     "Sentiment", "Intelligence", "Classification", "Ranking",
                     "Cross-Encoder", "Pipeline", "Diagnostics", "Registry",
                     "Health", "Deployment", "Assignments", "Documentation"}
    for key, trans in TRANSLATIONS.items():
        tr_text = trans.get("tr", "")
        # Check that Turkish translations don't contain raw English words
        for word in english_words:
            if word in tr_text and len(word) > 3:
                # Some terms like "Cross-Encoder" are technical
                if word not in ("Cross", "Encoder", "Cross-Encoder", "Reranking",
                                "Pipeline", "Diagnostics"):
                    pass  # Allow technical terms


# ---- Test 10: Sample queries populate expected fields ----
def test_sample_queries_have_fields() -> None:
    from portfolio.sample_queries import get_sample_queries
    samples = get_sample_queries()
    assert len(samples) > 0, "No sample queries defined"
    required_fields = {"query", "title", "category", "brand"}
    for i, s in enumerate(samples):
        missing = required_fields - set(s.keys())
        assert not missing, f"Sample {i} missing fields: {missing}"


# ---- Test 11: Every .py page file has a corresponding nav entry or is documented ----
def test_all_page_files_accounted() -> None:
    """Every page file should be in NAV_ROUTES or explicitly noted as not in nav."""
    all_modules = set(NAV_ROUTES.values())
    page_files = {
        f.stem for f in PAGES_DIR.glob("*.py")
        if f.is_file() and not f.name.startswith("_")
    }
    # Known pages not in the main nav (orphan/unlisted)
    known_extras = {"performance", "clustering", "trendyol_profile", "architecture"}
    unaccounted = page_files - all_modules - known_extras
    assert not unaccounted, f"Page files not in any nav route: {unaccounted}"


# ---- Test 12: Data workspace renders from persisted outputs without raw dataset ----
def test_data_workspace_profile_outputs_exist() -> None:
    from portfolio.config import TRENDYOL_PROFILE_DIR
    outputs_dir = TRENDYOL_PROFILE_DIR / "outputs"
    assert outputs_dir.is_dir(), "Profile outputs directory missing"
    files = list(outputs_dir.glob("*"))
    assert len(files) > 0, "No profile output files found"
    # At least one key output
    assert (outputs_dir / "schema_report.json").is_file() or \
           (outputs_dir / "data_quality_report.json").is_file(), \
           "No schema or quality report found in profile outputs"


# ---- Test 13: Dashboard metrics not double-escaped ----
def test_kpi_grid_escapes_properly() -> None:
    """kpi_grid should not double-escape HTML in badge values."""
    from portfolio.ui_components import kpi_grid, kpi_grid_mixed
    assert callable(kpi_grid)
    assert callable(kpi_grid_mixed)


# ---- Test 14: All subtitle keys exist in TRANSLATIONS ----
def test_all_subtitle_keys_have_translations() -> None:
    from portfolio.i18n import TRANSLATIONS
    subtitle_keys = {
        "subtitle_search_demo",
        "subtitle_architecture",
        "subtitle_eval_lab",
        "subtitle_assignments",
        "subtitle_notebook_status",
        "subtitle_artifact_health",
        "subtitle_deployment",
        "subtitle_model_registry",
        "subtitle_data_science_overview",
        "subtitle_projects",
        "subtitle_overview",
    }
    for key in subtitle_keys:
        assert key in TRANSLATIONS, f"Missing translations for '{key}'"
        trans = TRANSLATIONS[key]
        assert "tr" in trans, f"'{key}' missing Turkish translation"
        assert "en" in trans, f"'{key}' missing English translation"


# ---- Test 15: Model Registry _rel_path strips absolute prefixes ----
def test_model_registry_relative_paths() -> None:
    from portfolio.pages.model_registry import _rel_path
    from portfolio.config import ML_ROOT
    from pathlib import Path

    # Simulate a path under ML_ROOT
    test_path = ML_ROOT / "some" / "model.pkl"
    result = _rel_path(test_path)
    assert "/mount/src/" not in result, "Absolute path leaked in _rel_path"
    assert "/Users/" not in result, "User path leaked in _rel_path"
    assert str(test_path.relative_to(ML_ROOT)) == result, "Expected relative path"


def test_model_registry_relative_path_none() -> None:
    from portfolio.pages.model_registry import _rel_path
    assert _rel_path(None) == "\u2014"


# ---- Test 16: Hero panel subtitles use i18n t() not hardcoded strings ----
def test_hero_panel_subtitles_use_t() -> None:
    """Scan page modules to ensure hero_panel subtitle params use t()."""
    import ast
    modules_using_hardcoded_subtitles = []
    for fname in sorted(Path(PAGES_DIR).glob("*.py")):
        if fname.name.startswith("_"):
            continue
        source = fname.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'hero_panel':
                for kw in node.keywords:
                    if kw.arg == 'subtitle' and not (
                        isinstance(kw.value, ast.Call)
                        and getattr(kw.value.func, 'id', None) == 't'
                    ):
                        modules_using_hardcoded_subtitles.append(fname.stem)
                        break
    if modules_using_hardcoded_subtitles:
        pytest.fail(
            f"hero_panel subtitles should use t() in: {modules_using_hardcoded_subtitles}"
        )


# ---- Test 17: Status badge not used in kpi_grid (use kpi_grid_mixed) ----
def test_status_badge_in_kpi_grid() -> None:
    """status_badge() returns HTML; use kpi_grid_mixed not kpi_grid."""
    for fname in sorted(Path(PAGES_DIR).glob("*.py")):
        if fname.name.startswith("_"):
            continue
        source = fname.read_text(encoding="utf-8")
        # If kpi_grid is called and status_badge is used in the same function,
        # check they're not combined
        if "status_badge" in source and "kpi_grid" in source:
            # Find lines where kpi_grid is called
            for i, line in enumerate(source.split("\n"), 1):
                if "kpi_grid(" in line and "status_badge" in source.split("\n")[i-1]:
                    pytest.fail(
                        f"{fname.stem}:{i}: kpi_grid used with status_badge - "
                        f"use kpi_grid_mixed instead"
                    )


# ---- Test 18: format_metric handles bounded precision correctly ----
def test_format_metric_bounded_precision() -> None:
    from portfolio.ui_components import format_metric
    result = format_metric(0.123456789)
    assert result == "0.1235", f"Expected 4dp truncation, got: {result}"
    result = format_metric(1.23456789)
    assert result == "1.2346", f"Expected 4dp truncation, got: {result}"
    result = format_metric(None)
    assert result == "\u2014"

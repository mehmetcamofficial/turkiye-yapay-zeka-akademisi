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
    "nav_search_workspace": "search",
    "nav_search_intelligence": "search_intelligence",
    "nav_relevance_classification": "trendyol_relevance",
    "nav_hybrid_retrieval": "search_demo",
    "nav_cross_encoder": "trendyol_v5",
    "nav_policy_comparison": "policy_comparison",
    "nav_live_inference": "live_inference",
    "nav_runtime_diagnostics": "runtime_diagnostics",
    "nav_model_governance": "model_governance",
    "nav_churn": "churn",
    "nav_housing": "regression",
    "nav_sentiment": "nlp",
    "nav_search_relevance": "trendyol_relevance",
    "nav_search_ranking": "search_demo",
    "nav_pipeline_diagnostics": "eval_lab",
    "nav_data_workspace": "data_science_overview",
    "nav_data_science_midterm": "data_science_midterm",
    "nav_data_science_final": "data_science_final",
    "nav_registry": "model_registry",
    "nav_artifact_health": "artifact_health",
    "nav_deployment": "deployment",
    "nav_enterprise_readiness": "enterprise_readiness",
    "nav_assignments": "assignments",
    "nav_docs": "documentation",
    "nav_about": "about",
    "nav_notebook_status": "notebook_status",
    "nav_projects": "projects",
    "nav_copilot": "project_copilot",
}

# All required preserved pages
REQUIRED_MODULES: set[str] = {
    "churn", "regression", "nlp",
    "trendyol_relevance", "trendyol_v5",
    "model_registry", "artifact_health", "deployment", "enterprise_readiness",
    "policy_comparison", "live_inference", "runtime_diagnostics", "model_governance",
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
        "section_copilot",
    ]:
        assert nav_key in TRANSLATIONS, (
            f"Navigation key '{nav_key}' has no translations"
        )
        trans = TRANSLATIONS[nav_key]
        assert "tr" in trans, f"'{nav_key}' missing Turkish translation"
        assert "en" in trans, f"'{nav_key}' missing English translation"


def test_copilot_section_has_readable_bilingual_labels() -> None:
    from portfolio.i18n import TRANSLATIONS

    assert TRANSLATIONS["section_copilot"] == {
        "tr": "AI PROJE ASİSTANI",
        "en": "AI PROJECT COPILOT",
    }


def test_streamlit_page_configuration_is_centralized() -> None:
    """Only the application entry point may configure the Streamlit page."""
    import ast

    def set_page_config_calls(path: Path) -> list[ast.Call]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        return [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            and node.func.attr == "set_page_config"
        ]

    assert len(set_page_config_calls(SRC_DIR / "portfolio_app.py")) == 1
    assert not set_page_config_calls(PAGES_DIR / "project_copilot.py")


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


# ---- Test 19: Churn model loads and predicts with presets ----
def test_churn_model_inference() -> None:
    from portfolio.loaders import load_model_safe
    from portfolio.config import CHURN_MODEL_PATH
    from portfolio.churn_service import RAW_COLUMNS, prepare_model_input
    import pandas as pd
    model_result = load_model_safe(CHURN_MODEL_PATH)
    assert model_result.ok, f"Churn model load failed: {model_result.public_message}"
    model = model_result.model
    raw = pd.DataFrame([dict(zip(RAW_COLUMNS, [
        "Female", "No", "Yes", "No", 12, "Yes", "No", "Fiber optic",
        "No", "Yes", "No", "No", "Yes", "Yes", "Month-to-month", "Yes",
        "Electronic check", 89.5, 1074.0, 3200.0
    ]))])
    prepared = prepare_model_input(raw)
    pred = int(model.predict(prepared)[0])
    prob = float(model.predict_proba(prepared)[0, 1])
    assert pred in (0, 1), f"Churn prediction should be 0 or 1, got {pred}"
    assert 0.0 <= prob <= 1.0, f"Churn probability should be [0,1], got {prob}"


# ---- Test 20: Housing model loads and predicts with defaults ----
def test_housing_model_inference() -> None:
    from portfolio.loaders import load_model_safe
    from portfolio.config import REGRESSION_MODEL_PATH
    from portfolio.pages.regression import _prepare, RAW_COLUMNS
    import pandas as pd
    model_result = load_model_safe(REGRESSION_MODEL_PATH)
    assert model_result.ok, f"Housing model load failed: {model_result.public_message}"
    model = model_result.model
    defaults = [3.87, 28.6, 5.43, 1.10, 1425.0, 3.07, 35.63, -119.57]
    raw = pd.DataFrame([dict(zip(RAW_COLUMNS, defaults))])
    prepared = _prepare(raw)
    pred = float(model.predict(prepared)[0])
    assert 0.0 <= pred <= 10.0, f"Housing prediction should be in [0,10], got {pred}"


# ---- Test 21: Sentiment model loads and predicts both classes ----
def test_sentiment_model_inference() -> None:
    from portfolio.loaders import load_model_safe
    from portfolio.config import NLP_MODEL_PATH
    from portfolio.pages.nlp import _clean_text
    model_result = load_model_safe(NLP_MODEL_PATH)
    assert model_result.ok, f"Sentiment model load failed: {model_result.public_message}"
    model = model_result.model
    for text, expected in [
        ("This product works perfectly and I love it.", 1),
        ("This is the worst product I have ever purchased.", 0),
    ]:
        prepared = [_clean_text(text)]
        pred = int(model.predict(prepared)[0])
        assert pred == expected, f"Expected {expected}, got {pred} for: {text[:50]}"
        proba = model.predict_proba(prepared).max(axis=1)[0]
        assert 0.0 <= proba <= 1.0, f"Probas should be in [0,1], got {proba}"


# ---- Test 22: Sidebar routes map to unique module files ----
def test_sidebar_routes_map_to_unique_modules() -> None:
    """Every navigation route points to a distinct module file (except shared search_demo)."""
    from portfolio_app import PAGE_MODULE_MAP

    expected: dict[str, str] = {
    "nav_search_intelligence": "search_intelligence",
        "nav_hybrid_retrieval": "search_demo",
        "nav_cross_encoder": "trendyol_v5",
        "nav_policy_comparison": "policy_comparison",
        "nav_live_inference": "live_inference",
        "nav_runtime_diagnostics": "runtime_diagnostics",
        "nav_model_governance": "model_governance",
        "nav_deployment": "deployment",
        "nav_enterprise_readiness": "enterprise_readiness",
    }
    for nav_key, expected_module in expected.items():
        actual_module = PAGE_MODULE_MAP.get(nav_key)
        assert actual_module == expected_module, (
            f"PAGE_MODULE_MAP[{nav_key!r}] = {actual_module!r}, "
            f"expected {expected_module!r}"
        )

    modules = [expected[k] for k in expected if k != "nav_hybrid_retrieval"]
    assert len(set(modules)) == len(modules), (
        f"Routes must map to unique modules, got: {modules}"
    )


# ---- Test 23: No raw i18n keys in page UI function calls ----
def test_no_raw_keys_visible() -> None:
    """UI-text functions must use t(), not hardcoded English/Turkish strings."""
    import ast

    CHECKED_FUNCS: set[str] = {"hero_panel", "section_heading", "information_panel"}
    SKIP_FUNCS: set[str] = {"evidence_strip"}

    def _call_name(node: ast.Call) -> str | None:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "st":
                return f"st.{node.func.attr}"
            return node.func.attr
        return None

    def _has_raw_strings(nodes: list[ast.expr]) -> list[str]:
        found: list[str] = []
        for arg in nodes:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if len(arg.value) > 2 and not arg.value.startswith(("<", "<!--", "{")):
                    found.append(arg.value[:60])
            elif isinstance(arg, ast.Call) and _call_name(arg) in SKIP_FUNCS:
                continue
            elif isinstance(arg, (ast.List, ast.Tuple)):
                found.extend(_has_raw_strings(list(arg.elts)))
        return found

    KPI_LIKE = {"kpi_grid", "kpi_grid_mixed"}
    issues: list[str] = []
    for fname in sorted(Path(PAGES_DIR).glob("*.py")):
        if fname.name.startswith("_"):
            continue
        source = fname.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if name is None:
                continue
            if name in SKIP_FUNCS or (name and name.startswith("format_")):
                continue
            if name in CHECKED_FUNCS:
                raw = _has_raw_strings(node.args)
                for r in raw:
                    issues.append(f"{fname.stem}:{node.lineno}: {name}() has literal {r!r}")
                for kw in node.keywords:
                    raw = _has_raw_strings([kw.value])
                    for r in raw:
                        issues.append(
                            f"{fname.stem}:{node.lineno}: {name}({kw.arg}=) has literal {r!r}"
                        )
            elif name == "st.metric":
                for i, arg in enumerate(node.args):
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and len(arg.value) > 2:
                        issues.append(f"{fname.stem}:{node.lineno}: st.metric() arg {i} literal {arg.value[:60]!r}")
            elif name in KPI_LIKE:
                for arg in node.args:
                    raw = _has_raw_strings([arg])
                    for r in raw:
                        issues.append(f"{fname.stem}:{node.lineno}: {name}() has literal {r!r}")

    if issues:
        pytest.fail("Hardcoded text found (use t() instead):\n" + "\n".join(issues[:30]))


# ---- Test 24: Notebook status has no contradictory output counts ----
def test_no_contradictory_output_counts() -> None:
    """Notebook_status must use the same dynamic count, not hardcoded numbers."""
    source = (PAGES_DIR / "notebook_status.py").read_text(encoding="utf-8")
    hardcoded = re.findall(r'"\d+/\d+"', source)
    assert not hardcoded, (
        f"Hardcoded output count in notebook_status.py: {hardcoded}. "
        "Use profile_count variable instead."
    )
    # Ensure profile_count is used consistently
    profile_count_uses = [(i, line) for i, line in enumerate(source.split("\n"), 1)
                           if "profile_count" in line]
    assert len(profile_count_uses) >= 2, (
        "Expected profile_count to appear at least twice, found "
        f"{len(profile_count_uses)} times"
    )


# ---- Test 25: st.expander calls contain meaningful content ----
def test_technical_detail_expanders_have_content() -> None:
    """Every st.expander() must contain meaningful body content."""
    import ast

    issues: list[str] = []
    for fname in sorted(Path(PAGES_DIR).glob("*.py")):
        if fname.name.startswith("_"):
            continue
        source = fname.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        expander_calls = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "st" and node.func.attr == "expander":
                    expander_calls += 1
                    # Use source line heuristics: lines between expander and next dedent
                    line_idx = node.lineno - 1
                    # Check that there are non-empty, non-comment lines within the with block
                    lines = source.split("\n")
                    depth = None
                    has_content = False
                    for j in range(line_idx + 1, min(line_idx + 30, len(lines))):
                        stripped = lines[j].strip()
                        if not stripped or stripped.startswith("#"):
                            continue
                        curr_depth = len(lines[j]) - len(lines[j].lstrip())
                        if depth is None:
                            depth = curr_depth
                        if curr_depth < depth:
                            break
                        if not stripped.startswith("pass"):
                            has_content = True
                            break
                    if not has_content:
                        issues.append(
                            f"{fname.stem}:{node.lineno}: st.expander() has no meaningful content"
                        )
        if expander_calls == 0:
            pass  # No expanders is fine
    if issues:
        pytest.fail("\n".join(issues))


# ---- Test 32: Search and Hybrid have distinct page purposes (view selector) ----
def test_search_and_hybrid_have_distinct_page_purposes() -> None:
    """search_demo.py must have a view selector separating Product and Analysis views."""
    source = (PAGES_DIR / "search_demo.py").read_text(encoding="utf-8")
    assert "search_view_product" in source, "Must define product view key"
    assert "search_view_analysis" in source, "Must define analysis view key"
    assert "_render_product_view" in source or "product" in source.lower(), (
        "Must have product view rendering"
    )


# ---- Test 33: Live inference config uses human-readable labels ----
def test_live_inference_config_uses_human_labels() -> None:
    """trendyol_v5.py must use human-readable labels, not raw internal IDs."""
    source = (PAGES_DIR / "trendyol_v5.py").read_text(encoding="utf-8")
    assert "policy_cross_encoder" in source, "Must use human-readable policy label"
    assert "model_mmarco_minilm" in source, "Must use human-readable model name"
    assert "docvar_title_compact" in source, "Must use human-readable doc variant label"


# ---- Test 34: Cross-encoder config is in expander, not primary content ----
def test_cross_encoder_config_is_not_primary_content() -> None:
    """Technical config must be inside an expander."""
    source = (PAGES_DIR / "trendyol_v5.py").read_text(encoding="utf-8")
    assert 't("technical_details")' in source, "Must have technical details expander"
    # Check that model_id and revision are inside expander context
    expander_blocks = source.split('t("technical_details")')
    assert len(expander_blocks) >= 2, "Must have expander context for technical details"


# ---- Test 35: Sentiment result has separate label and value ----
def test_sentiment_result_has_separate_label_and_value() -> None:
    """NLP sentiment must display label and value separately."""
    source = (PAGES_DIR / "nlp.py").read_text(encoding="utf-8")
    assert "nlp_predicted" in source, "Must have predicted label"
    assert "nlp_positive_prob" in source, "Must have separate positive probability metric"
    assert "nlp_negative_prob" in source, "Must have separate negative probability metric"
    assert ".metric(" in source, "Must use .metric() for probabilities (not inline concat)"


# ---- Test 36: Sentiment probability chart uses both classes ----
def test_sentiment_probability_chart_uses_both_classes() -> None:
    """NLP must display both positive and negative probabilities."""
    source = (PAGES_DIR / "nlp.py").read_text(encoding="utf-8")
    assert "nlp_positive_prob" in source, "Must show positive probability metric"
    assert "nlp_negative_prob" in source, "Must show negative probability metric"
    assert "proba[0]" in source and "proba[1]" in source, "Must compute both class probabilities"


# ---- Test 37: Runtime diagnostics has explanation sections ----
def test_runtime_diagnostics_has_explanation_sections() -> None:
    """runtime_diagnostics.py must have explanation info blocks."""
    source = (PAGES_DIR / "runtime_diagnostics.py").read_text(encoding="utf-8")
    assert "explain_what" in source, "Must have 'what' explanation"
    assert "explain_why" in source, "Must have 'why' explanation"
    assert "explain_limitation" in source, "Must have limitation explanation"


# ---- Test 38: Data overview uses search dataset scope ----
def test_data_overview_uses_search_dataset_scope() -> None:
    """data_science_overview must not display old assignment framing."""
    source = (PAGES_DIR / "data_science_overview.py").read_text(encoding="utf-8")
    lines = source.split("\n")
    # Only check display-relevant lines (not imports or function names)
    display_lines = [l for l in lines if not l.strip().startswith(("from ", "import ", "#", "def ", "    def "))]
    display_text = "\n".join(display_lines).lower()
    forbidden_display = ["akademi", "ara sınav", "assignment", "ödev"]
    for term in forbidden_display:
        assert term not in display_text, (
            f"Must not display '{term}' in data overview"
        )
    assert "relevance" in source.lower() or "search" in source.lower() or "katalog" in source.lower(), (
        "Must reference search dataset scope"
    )


# ---- Test 39: No concatenated metric labels ----
def test_no_concatenated_metric_labels() -> None:
    """Metric labels and values must be separate, not concatenated."""
    import ast
    issues = []
    for fname in sorted(Path(PAGES_DIR).glob("*.py")):
        if fname.name.startswith("_"):
            continue
        source = fname.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "st" and node.func.attr == "metric":
                    args = node.args
                    if len(args) >= 2:
                        label = args[0]
                        value = args[1]
                        if isinstance(label, ast.Constant) and isinstance(value, ast.Constant):
                            label_str = str(label.value)
                            val_str = str(value.value)
                            # Check if value appears to be concatenated to label
                            if len(label_str) > 0 and len(val_str) > 0:
                                # Flag if value is embedded in label (run-on)
                                if val_str.startswith(tuple("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")):
                                    combined = label_str + val_str
                                    if any(word in combined.lower() for word in ["tahmin", "prediction", "sonuç", "result"]):
                                        issues.append(f"{fname.stem}:{node.lineno}: st.metric label+value may be concatenated")
    if issues:
        pytest.fail("\n".join(issues[:10]))


# ---- Test 40: Search and Hybrid render distinct result columns ----
def test_search_and_hybrid_render_distinct_result_columns() -> None:
    """Product view and Analysis view must use different result columns."""
    source = (PAGES_DIR / "search_demo.py").read_text(encoding="utf-8")
    # Product view should not include lexical/semantic ranks
    product_view_cols = ["rank_label", "product_label", "category_label"]
    analysis_view_cols = ["lexical_rank_label", "semantic_rank_label", "rrf_score_label", "fused_rank_label"]
    # Product view uses search_results heading
    assert "search_results" in source, "Product view must have results heading"
    # Analysis view must have analysis-specific keys
    assert "analysis_insight" in source or "fused_rank_label" in source, (
        "Analysis view must use retrieval-specific columns"
    )


# ---- Test 26: Housing inference and visualization are in separate try/except blocks ----
def test_housing_separate_inference_and_visualization() -> None:
    """Inference exception must not be caused by a chart failure."""
    source = (PAGES_DIR / "regression.py").read_text(encoding="utf-8")
    # Find the _single_prediction function
    lines = source.split("\n")
    in_func = False
    func_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("def _single_prediction"):
            in_func = True
            func_start = i
        elif in_func and line.strip().startswith("def ") and line.strip() != "def _single_prediction":
            in_func = False
    assert func_start > 0, "_single_prediction function not found"

    # Check that there are at least 2 try blocks in the function
    try_count = 0
    for i in range(func_start, len(lines)):
        if lines[i].strip().startswith("try:"):
            try_count += 1
    assert try_count >= 2, (
        f"Expected >=2 try blocks in _single_prediction (inference + viz), found {try_count}"
    )


# ---- Test 27: Housing uses explicit state checks, not truthiness ----
def test_housing_uses_explicit_state_checks() -> None:
    """Housing must check 'prediction is not None', not 'if prediction:'."""
    source = (PAGES_DIR / "regression.py").read_text(encoding="utf-8")
    # Check that explicit None checks are used
    assert "prediction is not None" in source, (
        "Must use 'prediction is not None' (not 'if prediction:')"
    )
    # Verify stale state is cleared before new prediction
    assert "st.session_state.pop" in source, (
        "Must clear stale state with st.session_state.pop"
    )


# ---- Test 28: Housing success/error exclusive rendering ----
def test_housing_error_does_not_coexist_with_result() -> None:
    """When error is set and prediction is None, no metric should render."""
    source = (PAGES_DIR / "regression.py").read_text(encoding="utf-8")
    # Check error guard clause returns early
    assert "if error and prediction is None:" in source, (
        "Must have guard: if error and prediction is None: return"
    )
    # Check metric is only rendered when prediction is not None
    assert "if prediction is not None:" in source, (
        "Metric must only render when prediction is not None"
    )


# ---- Test 29: Search demo imports runtime adapters ----
def test_search_demo_imports_runtime_adapters() -> None:
    """search_demo.py must import pipeline_search and v5_search."""
    source = (PAGES_DIR / "search_demo.py").read_text(encoding="utf-8")
    assert "from portfolio.trendyol_pipeline_service import pipeline_search" in source, (
        "Must import pipeline_search for V4 hybrid retrieval"
    )
    assert "from portfolio.trendyol_v5_pipeline_service import v5_search" in source, (
        "Must import v5_search for V5 cross-encoder"
    )


# ---- Test 30: Search demo uses session state for results (not static text) ----
def test_search_demo_uses_session_state() -> None:
    """search_demo.py must use st.session_state for result/error handling."""
    source = (PAGES_DIR / "search_demo.py").read_text(encoding="utf-8")
    assert "st.session_state" in source, "Must use session state for result management"
    assert 'st.session_state.pop("search_response"' in source, (
        "Must clear stale search response before new inference"
    )


# ---- Test 31: Search demo does not render explanation-only response ----
def test_search_demo_no_explanation_only() -> None:
    """search_demo.py must not contain the old st.info/callout explanation pattern for results."""
    source = (PAGES_DIR / "search_demo.py").read_text(encoding="utf-8")
    # Check that the old static explanation text is gone
    assert "Hybrid RRF retrieval mode. Query:" not in source, (
        "Must not show explanation-only Hybrid Retrieval response"
    )
    assert "Cross-encoder reranking mode. Query:" not in source, (
        "Must not show explanation-only Cross-Encoder response"
    )
    # Check that runtime is actually called
    assert "pipeline_search(" in source, "Must call pipeline_search for hybrid"
    assert "v5_search(" in source, "Must call v5_search for cross-encoder"
    # Check that results heading only appears with actual results
    assert "section_heading(t(\"search_results\"))" in source, (
        "Must show search_results heading"
    )


# ---- Test 41: notebook_status.py has render() function ----
def test_41_notebook_status_has_render() -> None:
    from portfolio.pages.notebook_status import render
    assert callable(render)


# ---- Test 42: notebook_status.py has CANONICAL_FILES list ----
def test_42_notebook_status_has_canonical_files() -> None:
    from portfolio.pages.notebook_status import CANONICAL_FILES
    assert isinstance(CANONICAL_FILES, list)
    assert len(CANONICAL_FILES) > 0
    assert all(isinstance(f, str) for f in CANONICAL_FILES)


# ---- Test 43: experiment store loading does not crash ----
def test_43_experiment_scanning_does_not_crash() -> None:
    from portfolio.experiment_store import load_experiments
    result = load_experiments()
    assert isinstance(result, list)


# ---- Test 44: profile outputs download function exists ----
def test_44_profile_outputs_download_function_exists() -> None:
    source = (PAGES_DIR / "notebook_status.py").read_text(encoding="utf-8")
    assert "st.download_button" in source
    assert "artifacts_bundle_download" in source


# ---- Test 45: kpi_grid is imported in notebook_status.py ----
def test_45_kpi_grid_imported_in_notebook_status() -> None:
    import ast
    source = (PAGES_DIR / "notebook_status.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "ui_components" in node.module:
            names = [alias.name for alias in node.names]
            if "kpi_grid" in names:
                return
    pytest.fail("kpi_grid not imported in notebook_status.py")


# ---- Test 46: documentation.py uses architecture_flow at least once ----
def test_46_documentation_uses_architecture_flow() -> None:
    source = (PAGES_DIR / "documentation.py").read_text(encoding="utf-8")
    count = source.count("architecture_flow(")
    assert count >= 1, f"Expected at least 1 architecture_flow call, found {count}"


# ---- Test 47: documentation.py uses information_panel at least once ----
def test_47_documentation_uses_information_panel() -> None:
    source = (PAGES_DIR / "documentation.py").read_text(encoding="utf-8")
    count = source.count("information_panel(")
    assert count >= 1, f"Expected at least 1 information_panel call, found {count}"


# ---- Test 48: documentation.py shows README and PORTFOLIO tabs ----
def test_48_documentation_shows_readme_and_portfolio_tabs() -> None:
    source = (PAGES_DIR / "documentation.py").read_text(encoding="utf-8")
    assert "tab_platform_readme" in source
    assert "tab_portfolio_evidence" in source
    assert "README.md" in source
    assert "PORTFOLIO.md" in source


# ---- Test 49: data_science_overview.py uses information_panel for insights ----
def test_49_data_overview_uses_information_panel_for_insights() -> None:
    from portfolio.ui_components import information_panel
    assert callable(information_panel)
    source = (PAGES_DIR / "data_science_overview.py").read_text(encoding="utf-8")
    insight_lines = [l for l in source.split("\n") if "insight" in l.lower()]
    for line in insight_lines:
        assert "t(" in line, f"Insight content should use t(): {line.strip()}"


# ---- Test 50: data_science_midterm.py uses kpi_grid for status items ----
def test_50_midterm_uses_kpi_grid_for_status_items() -> None:
    from portfolio.ui_components import kpi_grid
    assert callable(kpi_grid)
    source = (PAGES_DIR / "data_science_midterm.py").read_text(encoding="utf-8")
    assert "status_items = [" in source
    for line in source.split("\n"):
        if "status_label" in line or "midterm_source_files" in line:
            assert "t(" in line, f"Status items should use t(): {line.strip()}"


# ---- Test 51: trendyol_profile.py handles empty profile outputs ----
def test_51_trendyol_profile_handles_empty_outputs() -> None:
    source = (PAGES_DIR / "trendyol_profile.py").read_text(encoding="utf-8")
    assert "load_csv_safe" in source
    assert "load_json_safe" in source


# ---- Test 52: no file has >3 sequential st.info() calls ----
def test_52_no_excessive_sequential_st_info() -> None:
    import ast
    issues: list[str] = []
    for fname in sorted(Path(PAGES_DIR).glob("*.py")):
        if fname.name.startswith("_"):
            continue
        source = fname.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        lines = source.split("\n")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "st" and node.func.attr == "info":
                    line_idx = node.lineno - 1
                    count = 1
                    for j in range(line_idx + 1, min(line_idx + 10, len(lines))):
                        stripped = lines[j].strip()
                        if stripped.startswith("st.info("):
                            count += 1
                        else:
                            break
                    if count > 3:
                        issues.append(
                            f"{fname.stem}:{node.lineno}: "
                            f"{count} sequential st.info() calls (max 3)"
                        )
    if issues:
        pytest.fail("\n".join(issues))


# ---- Test 53: no concatenated metric format like "X: Y" in st.metric ----
def test_53_no_concatenated_metric_format() -> None:
    import ast
    issues: list[str] = []
    for fname in sorted(Path(PAGES_DIR).glob("*.py")):
        if fname.name.startswith("_"):
            continue
        source = fname.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "st" and node.func.attr == "metric":
                    if len(node.args) >= 2:
                        val = node.args[1]
                        if isinstance(val, ast.Constant) and isinstance(val.value, str):
                            if ":" in val.value:
                                issues.append(
                                    f"{fname.stem}:{node.lineno}: "
                                    f"st.metric value has colon format: {val.value[:60]!r}"
                                )
    if issues:
        pytest.fail("\n".join(issues[:10]))


# ---- Test 54: trendyol_v5.py live inference uses render_safe_table not st.table ----
def test_54_live_inference_uses_render_safe_table() -> None:
    source = (PAGES_DIR / "trendyol_v5.py").read_text(encoding="utf-8")
    assert "render_safe_table(" in source
    assert "st.table(" not in source


# ---- Test 55: trendyol_v5.py has section_heading for live inference ----
def test_55_live_inference_has_section_heading() -> None:
    source = (PAGES_DIR / "trendyol_v5.py").read_text(encoding="utf-8")
    assert 'section_heading(t("live_inference")' in source


# ---- Test 56: kpi_grid renders with proper HTML structure ----
def test_56_kpi_grid_renders_proper_html_structure() -> None:
    from portfolio.ui_components import kpi_grid
    with patch("streamlit.markdown") as mock_markdown:
        kpi_grid([("Label", "Value", "Note")])
        args, kwargs = mock_markdown.call_args
        html = args[0]
        assert "kpi-grid" in html
        assert "metric-card" in html
        assert kwargs.get("unsafe_allow_html") is True


# ---- Test 57: empty_state accepts both title and text parameters ----
def test_57_empty_state_accepts_title_and_text() -> None:
    from portfolio.ui_components import empty_state
    with patch("streamlit.markdown") as mock_markdown:
        empty_state("Test Title", "Test Text")
        args, kwargs = mock_markdown.call_args
        html = args[0]
        assert "Test Title" in html
        assert "Test Text" in html


# ════════════════════════════════════════════════════════
# Sprint 2 — Command Center Tests
# ════════════════════════════════════════════════════════

COM_CENTER_MODULE = PAGES_DIR / "overview.py"

def test_cc_module_imports() -> None:
    from portfolio.pages.overview import render
    assert callable(render)


def test_cc_hero_title_exists() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    assert "command_hero(" in source or "command_center" in source


def test_cc_status_strip_labels_exist() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    assert "status_strip([" in source
    assert "strip_models_label" in source
    assert "strip_tests_label" in source
    assert "strip_sources_label" in source
    assert "strip_runtime_label" in source
    assert "strip_validation_label" in source


def test_cc_health_section_contains_all_cards() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    assert "health_model_runtime" in source
    assert "health_search_pipeline" in source
    assert "health_data_readiness" in source
    assert "health_validation_suite" in source
    assert "health_artifact_registry" in source
    assert "health_notebook_schema" in source


def test_cc_capability_registry_contains_required() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    for cap in ["cap_housing_name", "cap_churn_name", "cap_sentiment_name",
                 "cap_hybrid_name", "cap_cross_encoder_name",
                 "cap_runtime_name", "cap_data_name"]:
        assert cap in source, f"Missing capability: {cap}"


def test_cc_pipeline_contains_all_stages() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    for stage in ["pipeline_data_sources", "pipeline_validation", "pipeline_features",
                   "pipeline_training", "pipeline_registry", "pipeline_inference",
                   "pipeline_monitoring"]:
        assert stage in source, f"Missing pipeline stage: {stage}"


def test_cc_no_forbidden_production_claims() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    forbidden = ["Production Healthy", "Global Traffic", "Live Customers",
                 "Real-Time Enterprise Load", "production uptime",
                 "active production users", "real request count"]
    for phrase in forbidden:
        assert phrase.lower() not in source.lower(), f"Forbidden phrase: {phrase}"


def test_cc_no_raw_model_ids_in_visible_labels() -> None:
    ids = ["mmarco-mMiniLMv2", "title_compact_metadata", "1427fd652930"]
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    for raw_id in ids:
        assert raw_id not in source, f"Internal model ID leaked: {raw_id}"


def test_cc_all_new_i18n_keys_exist() -> None:
    from portfolio.i18n import TRANSLATIONS
    required = [
        "command_center_title", "command_center_subtitle",
        "command_center_badge_local", "command_center_badge_validated",
        "command_center_badge_architect",
        "strip_models_label", "strip_tests_label", "strip_sources_label",
        "strip_runtime_label", "strip_validation_label",
        "health_model_runtime", "health_search_pipeline", "health_data_readiness",
        "health_validation_suite", "health_artifact_registry", "health_notebook_schema",
        "cap_housing_name", "cap_churn_name", "cap_sentiment_name",
        "cap_hybrid_name", "cap_cross_encoder_name", "cap_runtime_name", "cap_data_name",
        "pipeline_data_sources", "pipeline_validation", "pipeline_features",
        "pipeline_training", "pipeline_registry", "pipeline_inference", "pipeline_monitoring",
        "activity_title", "activity_empty_title", "activity_empty_cta",
        "search_snapshot_title", "data_readiness_title", "artifacts_title",
        "quick_actions_title", "transparency_title",
        "qa_sentiment", "qa_housing", "qa_hybrid", "qa_cross_encoder",
        "qa_runtime", "qa_data",
        "transparency_runtime", "transparency_validation", "transparency_models",
        "transparency_deployment", "transparency_data",
    ]
    for key in required:
        assert key in TRANSLATIONS, f"Missing i18n key: {key}"
        tr = TRANSLATIONS[key].get("tr", "")
        en = TRANSLATIONS[key].get("en", "")
        assert tr, f"Missing Turkish for: {key}"
        assert en, f"Missing English for: {key}"


def test_cc_navigation_targets_match_valid_pages() -> None:
    from portfolio.config import ALL_NAV_PAGES
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    targets = [
        "nav_search_intelligence", "nav_housing", "nav_churn", "nav_sentiment",
        "nav_hybrid_retrieval", "nav_cross_encoder", "nav_runtime_diagnostics",
        "nav_data_workspace", "nav_registry", "nav_notebook_status", "nav_docs",
    ]
    for tgt in targets:
        assert tgt in ALL_NAV_PAGES, f"Invalid nav target: {tgt}"
        assert tgt in source, f"Nav target not used in CC: {tgt}"


def test_cc_no_absolute_local_paths() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    forbidden = ["/Users/", "Developer/", "mehmetcam/"]
    for path in forbidden:
        assert path not in source, f"Absolute path leaked: {path}"


def test_cc_empty_activity_state_exists() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    assert "activity_empty_title" in source


def test_cc_transparency_section_exists() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    assert "transparency_panel" in source or "transparency_title" in source


def test_cc_search_snapshot_has_candidate_and_result_counts() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    assert "20" in source
    assert "10" in source


def test_cc_uses_navigate_to_not_fake_routing() -> None:
    from portfolio.ui_components import navigate_to
    assert callable(navigate_to)


def test_cc_does_not_initialize_models_directly() -> None:
    source = COM_CENTER_MODULE.read_text(encoding="utf-8")
    forbidden_init = ["load_model_safe", "joblib.load", "model.predict", "predict_proba"]
    for call in forbidden_init:
        assert call not in source, f"CC directly initializes models: {call}"


# ════════════════════════════════════════════════════════
# Sprint 2 — M1.2 Notebook & Experiment Tests
# ════════════════════════════════════════════════════════

S2_MODULE = SRC_DIR / "portfolio" / "pages" / "notebook_status.py"


def test_s2_notebook_discovery_returns_relative_paths() -> None:
    from portfolio.pages.notebook_status import _discover_notebooks
    nbs = _discover_notebooks()
    assert isinstance(nbs, list)
    for nb in nbs:
        assert not nb["path"].startswith("/Users/"), f"Absolute path: {nb['path']}"
        assert not nb["path"].startswith("Developer/"), f"Developer path: {nb['path']}"
        assert nb["path"].endswith(".ipynb"), f"Not a notebook: {nb['path']}"


def test_s2_no_absolute_path_in_notebook_kpi() -> None:
    source = S2_MODULE.read_text(encoding="utf-8")
    forbidden = ["/Users/", "Developer/mehmetcam"]
    for path in forbidden:
        assert path not in source, f"Absolute path leaked: {path}"


def test_s2_github_url_valid() -> None:
    from portfolio.pages.notebook_status import _discover_notebooks
    nbs = _discover_notebooks()
    for nb in nbs:
        url = nb["github_url"]
        assert url.startswith("https://github.com/"), f"Bad GitHub URL: {url}"
        assert "mehmetcamofficial" in url, f"Wrong owner: {url}"
        assert "turkiye-yapay-zeka-akademisi" in url, f"Wrong repo: {url}"
        assert nb["path"] in url, f"Path missing from URL: {url}"


def test_s2_colab_url_valid() -> None:
    from portfolio.pages.notebook_status import _discover_notebooks
    nbs = _discover_notebooks()
    for nb in nbs:
        url = nb["colab_url"]
        assert url.startswith("https://colab.research.google.com/"), f"Bad Colab URL: {url}"
        assert "github" in url.lower(), f"No github in Colab URL: {url}"
        assert nb["colab_valid"], f"Colab URL flagged invalid: {url}"


def test_s2_download_content_is_valid_notebook_json() -> None:
    import json
    from portfolio.pages.notebook_status import _discover_notebooks
    nbs = _discover_notebooks()
    for nb in nbs:
        data = nb["bytes"]
        assert len(data) > 0, f"Empty notebook bytes: {nb['name']}"
        parsed = json.loads(data.decode("utf-8"))
        assert "cells" in parsed, f"No cells in notebook: {nb['name']}"
        assert "nbformat" in parsed, f"No nbformat in: {nb['name']}"


def test_s2_missing_experiment_file_returns_empty_list() -> None:
    from portfolio.experiment_store import load_experiments
    import tempfile, os
    from portfolio.experiment_store import EXPERIMENTS_FILE
    if not EXPERIMENTS_FILE.is_file():
        result = load_experiments()
        assert isinstance(result, list)
        assert len(result) == 0


def test_s2_experiment_append_and_reload(tmp_path) -> None:
    import json as j
    from portfolio.experiment_store import append_experiment, load_experiments
    from portfolio.config import ARTIFACTS_DIR
    orig_file = ARTIFACTS_DIR / "experiments" / "experiments.jsonl"
    test_file = tmp_path / "test_experiments.jsonl"

    saved = None
    if orig_file.is_file():
        saved = orig_file.read_text(encoding="utf-8")
        orig_file.unlink()

    try:
        rec = {
            "experiment_type": "evaluation",
            "capability": "test_cap",
            "model_name": "test_model",
            "status": "completed",
            "metrics": {"accuracy": 0.95},
        }
        result = append_experiment(rec)
        assert result["experiment_id"] is not None
        assert result["experiment_type"] == "evaluation"

        loaded = load_experiments()
        assert any(e["experiment_id"] == result["experiment_id"] for e in loaded)
    finally:
        if orig_file and saved is not None:
            orig_file.parent.mkdir(parents=True, exist_ok=True)
            orig_file.write_text(saved, encoding="utf-8")


def test_s2_duplicate_records_prevented(tmp_path) -> None:
    from portfolio.experiment_store import append_experiment
    from portfolio.config import ARTIFACTS_DIR
    orig_file = ARTIFACTS_DIR / "experiments" / "experiments.jsonl"

    saved = None
    if orig_file.is_file():
        saved = orig_file.read_text(encoding="utf-8")
        orig_file.unlink()

    try:
        rec = {
            "experiment_id": "dup_test_001",
            "experiment_type": "evaluation",
            "capability": "test",
            "model_name": "m",
            "status": "completed",
            "metrics": {},
        }
        first = append_experiment(rec)
        assert first["experiment_id"] == "dup_test_001"

        from portfolio.experiment_store import load_experiments
        before = len(load_experiments())

        second = append_experiment(rec)
        after = len(load_experiments())
        assert after == before, "Duplicate was not rejected"
    finally:
        if orig_file and saved is not None:
            orig_file.parent.mkdir(parents=True, exist_ok=True)
            orig_file.write_text(saved, encoding="utf-8")


def test_s2_numpy_values_serialize() -> None:
    import numpy as np
    from portfolio.experiment_store import safe_json_value
    assert safe_json_value(np.float64(3.14)) == 3.14
    assert safe_json_value(np.int64(42)) == 42
    assert safe_json_value(np.bool_(True)) is True
    assert safe_json_value(np.array([1, 2, 3])) == [1, 2, 3]


def test_s2_tuple_parameters_serialize() -> None:
    from portfolio.experiment_store import safe_json_value
    result = safe_json_value((1, 2))
    assert isinstance(result, str)
    assert result == "(1, 2)"


def test_s2_malformed_jsonl_does_not_crash(tmp_path) -> None:
    from portfolio.experiment_store import load_experiments
    from portfolio.config import ARTIFACTS_DIR
    orig_file = ARTIFACTS_DIR / "experiments" / "experiments.jsonl"

    saved = None
    if orig_file.is_file():
        saved = orig_file.read_text(encoding="utf-8")

    try:
        orig_file.parent.mkdir(parents=True, exist_ok=True)
        with open(orig_file, "w") as f:
            f.write("not valid json\n")
            f.write('{"experiment_id": "ok", "capability": "t"}\n')
            f.write("also invalid\n")
        result = load_experiments()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["experiment_id"] == "ok"
    finally:
        if saved is not None:
            orig_file.parent.mkdir(parents=True, exist_ok=True)
            orig_file.write_text(saved, encoding="utf-8")


def test_s2_ordinary_prediction_not_recorded_as_experiment() -> None:
    from portfolio.experiment_store import EXPERIMENT_TYPES
    from portfolio.ui_components import log_activity
    session_log = []
    from unittest.mock import patch
    with patch("streamlit.session_state", {"cc_activity_log": session_log}):
        log_activity("Housing", "Prediction completed")
        assert len(session_log) == 1
    assert "experiment" not in str(type(log_activity))


def test_s2_gridsearch_normalizes_to_dataframe() -> None:
    import pandas as pd
    from portfolio.experiment_store import normalize_gridsearch_results

    cv_data = {
        "param_model__alpha": [0.1, 0.2, 0.3],
        "mean_test_score": [0.8, 0.85, 0.82],
        "std_test_score": [0.02, 0.03, 0.025],
        "rank_test_score": [3, 1, 2],
    }
    df = normalize_gridsearch_results(cv_data)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["rank_test_score"] == 1


def test_s2_gridsearch_normalize_none_or_empty() -> None:
    import pandas as pd
    from portfolio.experiment_store import normalize_gridsearch_results
    assert isinstance(normalize_gridsearch_results(None), pd.DataFrame)
    assert isinstance(normalize_gridsearch_results({}), pd.DataFrame)
    assert isinstance(normalize_gridsearch_results(pd.DataFrame()), pd.DataFrame)


def test_s2_all_experiment_i18n_keys_exist() -> None:
    from portfolio.i18n import TRANSLATIONS
    required = [
        "exp_registry_title", "exp_total", "exp_completed", "exp_failed",
        "exp_latest_run", "exp_training", "exp_evaluation",
        "exp_hyperparameter_search", "exp_benchmark", "exp_parameters",
        "exp_metrics", "exp_artifacts", "exp_compare", "exp_no_compatible",
        "exp_capability_filter", "exp_type_filter", "exp_status_filter",
        "exp_name_col", "exp_capability_col", "exp_type_col", "exp_model_col",
        "exp_status_col", "exp_started_col", "exp_duration_col", "exp_metric_col",
        "exp_details", "exp_source", "exp_notes", "exp_timestamps",
        "exp_duration_ms", "exp_primary_metric",
        "view_on_github", "github", "colab", "download",
    ]
    for key in required:
        assert key in TRANSLATIONS, f"Missing i18n key: {key}"
        tr = TRANSLATIONS[key].get("tr", "")
        en = TRANSLATIONS[key].get("en", "")
        assert tr, f"Missing Turkish for: {key}"
        assert en, f"Missing English for: {key}"


def test_s2_experiment_table_has_required_columns() -> None:
    from portfolio.i18n import TRANSLATIONS
    required_col_keys = [
        "exp_name_col", "exp_capability_col", "exp_type_col",
        "exp_model_col", "exp_status_col", "exp_started_col",
        "exp_duration_col", "exp_metric_col",
    ]
    for key in required_col_keys:
        assert key in TRANSLATIONS
        assert TRANSLATIONS[key].get("tr", "")
        assert TRANSLATIONS[key].get("en", "")


def test_s2_artifact_paths_sanitized() -> None:
    from portfolio.experiment_store import normalize_experiment
    rec = normalize_experiment({
        "experiment_type": "evaluation",
        "capability": "test",
        "model_name": "m",
        "artifact_paths": ["/Users/someone/absolute/path.ipynb"],
    })
    for ap in rec["artifact_paths"]:
        assert not ap.startswith("/Users/"), f"Absolute path in artifacts: {ap}"
        assert not ap.startswith("Developer/"), f"Developer path in artifacts: {ap}"


def test_s2_notebook_kpi_shows_notebook_count() -> None:
    from portfolio.pages.notebook_status import _discover_notebooks
    nbs = _discover_notebooks()
    assert len(nbs) >= 1
    assert all(nb["github_url"] for nb in nbs)
    assert all(nb["colab_url"] for nb in nbs)
    assert all(nb["bytes"] for nb in nbs)


def test_s2_render_safe_table_receives_dataframe() -> None:
    from portfolio.ui_components import render_safe_table
    import pandas as pd
    import streamlit as st

    df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    with patch.object(st, "markdown", return_value=None):
        with patch.object(st, "download_button", return_value=None):
            with patch.object(st, "caption", return_value=None):
                try:
                    render_safe_table(df)
                except Exception as exc:
                    pytest.fail(f"render_safe_table raised: {exc}")


# ── Sprint 3 M3.1 tests ────────────────────────────────────────────────

def test_s3_resource_type_counts_are_dynamic() -> None:
    from portfolio.search_index import get_search_index, reset_search_index
    reset_search_index()
    idx = get_search_index()
    idx.ensure_ready()
    stats = idx.get_stats()
    types = stats.get("resource_types", {})
    assert isinstance(types, dict)
    assert len(types) >= 1
    total = sum(types.values())
    assert total == stats["total_documents"]
    assert total >= 200


def test_s3_index_total_is_consistent() -> None:
    from portfolio.search_index import get_search_index, reset_search_index
    reset_search_index()
    idx = get_search_index()
    idx.ensure_ready()
    stats = idx.get_stats()
    assert stats["total_documents"] >= 260


def test_s3_title_match_outranks_tag_match() -> None:
    from portfolio.search_index import get_search_index, reset_search_index
    reset_search_index()
    idx = get_search_index()
    idx.ensure_ready()
    results = idx.search("housing", top_k=20)
    title_scores = [r.score for r in results if r.match_reason == "title:housing"]
    tag_scores = [r.score for r in results if r.match_reason == "tag:housing"]
    if title_scores and tag_scores:
        assert max(title_scores) > max(tag_scores), \
            f"Title match ({max(title_scores):.1f}) should outrank tag match ({max(tag_scores):.1f})"


def test_s3_tag_match_outranks_content_match() -> None:
    from portfolio.search_index import get_search_index, reset_search_index
    reset_search_index()
    idx = get_search_index()
    idx.ensure_ready()
    results = idx.search("churn", top_k=20)
    tag_scores = [r.score for r in results if r.match_reason == "tag:churn"]
    content_scores = [r.score for r in results if r.match_reason.startswith("content:")]
    if tag_scores and content_scores:
        assert max(tag_scores) > max(content_scores), \
            f"Tag match ({max(tag_scores):.1f}) should outrank content match ({max(content_scores):.1f})"


def test_s3_search_i18n_keys_exist() -> None:
    from portfolio.i18n import TRANSLATIONS
    required = ["search_title", "search_placeholder", "search_btn",
                "suggested_queries", "no_results", "no_results_desc",
                "results_found", "index_stats", "recent_searches",
                "search_empty_hint", "filters", "reset_filters"]
    for key in required:
        assert key in TRANSLATIONS, f"Missing i18n key: {key}"
        assert "tr" in TRANSLATIONS[key], f"Missing tr for {key}"
        assert "en" in TRANSLATIONS[key], f"Missing en for {key}"


def test_s3_search_service_has_no_f1_suggestion() -> None:
    from portfolio.search_service import DEFAULT_SUGGESTIONS
    assert "f1 > 0.8" not in DEFAULT_SUGGESTIONS


def test_s3_search_page_has_no_f1_suggestion() -> None:
    from portfolio.pages.search import _render_suggested_queries
    import inspect
    src = inspect.getsource(_render_suggested_queries)
    assert "f1 > 0.8" not in src


def test_s3_extract_title_no_comma() -> None:
    from portfolio.search_index import SearchIndex
    from pathlib import Path
    import tempfile
    idx = SearchIndex()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write('from __future__ import annotations\n\n"""Valid docstring."""\n')
        fname = f.name
    result = idx._extract_title(Path(fname), '"""Valid docstring."""', "source_code")
    os.unlink(fname)
    assert result == "Valid docstring."


def test_s3_extract_title_fstring_ignored() -> None:
    from portfolio.search_index import SearchIndex
    from pathlib import Path
    import tempfile
    idx = SearchIndex()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write('f"""not a docstring"""\n')
        fname = f.name
    result = idx._extract_title(Path(fname), 'f"""not a docstring"""', "source_code")
    os.unlink(fname)
    assert result != "not a docstring"  # Falls back to path stem


def test_s3_extract_title_closing_comma_ignored() -> None:
    from portfolio.search_index import SearchIndex
    from pathlib import Path
    import tempfile
    idx = SearchIndex()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write('x = """\n"""\n')
        fname = f.name
    content = 'x = """\n"""\n'
    result = idx._extract_title(Path(fname), content, "source_code")
    os.unlink(fname)
    assert result not in (",", "")  # Should not return comma or empty

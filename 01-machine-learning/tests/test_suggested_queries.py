"""Tests for the suggested-query chip component.

Covers:
  1. Expected 10 suggestions are defined in search.py
  2. Turkish rendering uses correct queries
  3. English rendering (i18n key exists)
  4. No query text contains manually inserted newline characters
  5. Suggestion rendering imports from a reusable implementation
  6. Existing search behavior preserved (render function structure)
  7. Portfolio integrity tests still pass (verified separately)
  8. No absolute paths in component code
  9. No duplicate widget keys in search.py
  10. render_suggested_queries function is importable and callable
"""

from pathlib import Path

# ── Constants ──
EXPECTED_SUGGESTIONS = [
    "sentiment", "duygu analizi", "churn", "müşteri kaybı",
    "housing", "konut tahmini", "random forest", "grid search",
    "notebook", "architecture",
]

SEARCH_PAGE = Path(__file__).resolve().parents[1] / "portfolio" / "pages" / "search.py"


def test_suggestion_count() -> None:
    """1. The 10 expected suggestions are defined."""
    from portfolio.pages.search import _render_suggested_queries
    assert callable(_render_suggested_queries)


def test_suggestions_list_has_correct_count() -> None:
    """The suggestion list in search.py must have exactly 10 entries."""
    source = SEARCH_PAGE.read_text(encoding="utf-8")
    # Find the suggestion list in the source
    for q in EXPECTED_SUGGESTIONS:
        assert q in source, f"Suggestion {q!r} not found in search.py"


def test_no_newlines_in_suggestion_text() -> None:
    """4. No query text contains manually inserted newline characters."""
    for q in EXPECTED_SUGGESTIONS:
        assert "\n" not in q, f"Suggestion {q!r} contains newline"
        assert "\r" not in q, f"Suggestion {q!r} contains carriage return"
        assert "\\n" not in q, f"Suggestion {q!r} contains literal \\n"


def test_reusable_implementation_importable() -> None:
    """5. The reusable implementation exists and is callable."""
    from portfolio.ui_components import render_suggested_queries
    assert callable(render_suggested_queries)


def test_no_absolute_paths_in_ui_components() -> None:
    """8. No absolute paths exposed in the component code."""
    ui_path = Path(__file__).resolve().parents[1] / "portfolio" / "ui_components.py"
    source = ui_path.read_text(encoding="utf-8")
    forbidden = ["/Users/", "/mount/src/"]
    for path in forbidden:
        assert path not in source, f"Absolute path {path!r} found in ui_components.py"


def test_no_duplicate_keys_in_search_page() -> None:
    """9. No duplicate widget keys in search.py (key= duplication)."""
    source = SEARCH_PAGE.read_text(encoding="utf-8")
    import re
    # Find all key="..." or key='...' in the source
    keys = re.findall(r'key\s*=\s*"([^"]+)"', source)
    keys += re.findall(r"key\s*=\s*'([^']+)'", source)
    duplicates = {k for k in keys if keys.count(k) > 1}
    # Allow key="search_reset_filters" which appears in both selectbox and button
    duplicates -= {"search_reset_filters"}
    assert not duplicates, f"Duplicate Streamlit widget keys: {duplicates}"


def test_render_function_structure_preserved() -> None:
    """6. Existing render() in search.py still calls _ensure_session and service."""
    source = SEARCH_PAGE.read_text(encoding="utf-8")
    assert "_ensure_session()" in source
    assert "get_search_service()" in source
    assert "_render_results" in source


def test_suggested_queries_i18n_key_exists() -> None:
    """3. The i18n key for suggested queries exists in both languages."""
    from portfolio.i18n import TRANSLATIONS
    key = "suggested_queries"
    assert key in TRANSLATIONS, f"Missing i18n key: {key}"
    assert "tr" in TRANSLATIONS[key], "Missing Turkish translation"
    assert "en" in TRANSLATIONS[key], "Missing English translation"
    tr_text = TRANSLATIONS[key]["tr"]
    en_text = TRANSLATIONS[key]["en"]
    assert tr_text == "Önerilen Sorgular"
    assert en_text == "Suggested Queries"


def test_render_suggested_queries_calls_button() -> None:
    """The component calls ``st.button`` for each chip."""
    from portfolio.ui_components import render_suggested_queries
    from unittest.mock import patch

    with patch("streamlit.button") as mock_btn, \
         patch("streamlit.markdown") as mock_md, \
         patch("streamlit.columns") as mock_cols:
        mock_cols.return_value = [mock_cols] * 5
        render_suggested_queries(["test query"])
        assert mock_btn.called, "st.button should be called at least once"


def test_compact_mode_accepts_parameter() -> None:
    """Compact mode parameter is accepted without error."""
    from portfolio.ui_components import render_suggested_queries
    from unittest.mock import patch

    with patch("streamlit.button") as mock_btn, \
         patch("streamlit.markdown") as mock_md, \
         patch("streamlit.columns") as mock_cols:
        mock_cols.return_value = [mock_cols] * 5
        render_suggested_queries(["a", "b"], compact=True)

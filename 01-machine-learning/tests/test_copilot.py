from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from portfolio.copilot.config import REPO_ROOT, INDEX_DIR
from portfolio.copilot.indexer import index_repository, save_index, load_index
from portfolio.copilot.retriever import retrieve, RetrievalConfig
from portfolio.copilot.intent import classify_intent
from portfolio.copilot.answer import generate_answer
from portfolio.copilot.citation import validate_citation, validate_citations
from portfolio.copilot.safety import is_secret_file, is_sensitive_content, is_within_repo
from portfolio.copilot.memory import ConversationMemory


def _chunk_for_path(file_path: str):
    from portfolio.copilot.schema import CopilotChunk

    return CopilotChunk(
        chunk_id="test:1",
        document_id="test",
        file_path=file_path,
        file_type="python",
        project_area="portfolio",
        text="test content",
        start_line=1,
        end_line=1,
        cell_index=None,
        cell_type=None,
    )


def test_exact_filename_stem_match_receives_fixed_bonus() -> None:
    from portfolio.copilot.retriever import EXACT_FILENAME_STEM_BONUS, exact_filename_stem_score

    assert exact_filename_stem_score({"regression"}, _chunk_for_path("portfolio/pages/regression.py")) == EXACT_FILENAME_STEM_BONUS


def test_partial_filename_stem_does_not_receive_bonus() -> None:
    from portfolio.copilot.retriever import exact_filename_stem_score

    assert exact_filename_stem_score({"regress"}, _chunk_for_path("portfolio/pages/regression.py")) == 0.0


def test_unrelated_filename_does_not_receive_stem_bonus() -> None:
    from portfolio.copilot.retriever import exact_filename_stem_score

    assert exact_filename_stem_score({"housing"}, _chunk_for_path("portfolio/pages/regression.py")) == 0.0


def test_repeated_exact_token_does_not_multiply_stem_bonus() -> None:
    from portfolio.copilot.retriever import EXACT_FILENAME_STEM_BONUS, _normalize_query, exact_filename_stem_score

    _, tokens = _normalize_query("i18n i18n i18n")
    assert exact_filename_stem_score(tokens, _chunk_for_path("portfolio/i18n.py")) == EXACT_FILENAME_STEM_BONUS


def test_nonmatching_stem_leaves_existing_score_unchanged() -> None:
    from portfolio.copilot.retriever import exact_filename_stem_score

    base_score = 2.5
    bonus = exact_filename_stem_score({"housing"}, _chunk_for_path("portfolio/pages/regression.py"))
    assert base_score + bonus == base_score


def test_turkish_search_alias_expands_arama() -> None:
    from portfolio.copilot.retriever import _normalize_query

    _, tokens = _normalize_query("arama projesi")
    assert "arama" in tokens
    assert "search" in tokens


def test_existing_turkish_alias_still_expands_envanter() -> None:
    from portfolio.copilot.retriever import _normalize_query

    _, tokens = _normalize_query("envanter")
    assert tokens == {"envanter", "inventory"}


def test_unrelated_token_is_not_rewritten() -> None:
    from portfolio.copilot.retriever import _normalize_query

    _, tokens = _normalize_query("benzersizkelime")
    assert tokens == {"benzersizkelime"}


def test_unsupported_alias_expands_to_existing_answer_behavior() -> None:
    from portfolio.copilot.retriever import _normalize_query

    _, tokens = _normalize_query("unsupported")
    assert {"unsupported", "answer", "no", "evidence", "limitations"} <= tokens


def test_no_evidence_answer_is_marked_unsupported() -> None:
    answer = generate_answer("unsupported question", [], intent="explain_code")
    assert answer.unsupported is True
    assert answer.confidence == "No evidence"
    assert answer.limitations is not None


def test_indexer_returns_chunks() -> None:
    chunks = index_repository(REPO_ROOT)
    assert len(chunks) > 0
    assert len(chunks) < 5000


def test_chunk_has_required_fields() -> None:
    chunks = index_repository(REPO_ROOT)
    if chunks:
        c = chunks[0]
        assert c.file_path != ""
        assert c.chunk_id != ""
        assert c.start_line is not None or c.cell_index is not None


def test_save_load_roundtrip() -> None:
    chunks = index_repository(REPO_ROOT)
    save_index(chunks, INDEX_DIR / "test_roundtrip.json")
    loaded = load_index(INDEX_DIR / "test_roundtrip.json")
    assert len(loaded) == len(chunks)


def test_empty_index_load() -> None:
    save_index([], INDEX_DIR / "empty_test.json")
    loaded = load_index(INDEX_DIR / "empty_test.json")
    assert len(loaded) == 0


def test_intent_classification_file() -> None:
    assert classify_intent("dosya nerede") == "find_file"


def test_intent_classification_compare() -> None:
    assert classify_intent("karşılaştır") == "compare_projects"


def test_intent_classification_summary() -> None:
    assert classify_intent("özetle") == "summarize_project"


def test_intent_classification_default() -> None:
    assert classify_intent("hello") == "general_repository_question"


def test_retrieval_returns_results() -> None:
    chunks = index_repository(REPO_ROOT)
    results = retrieve("MRR", chunks, RetrievalConfig(query_intent="explain_metric"))
    assert len(results) > 0


def test_retrieval_respects_max_results() -> None:
    chunks = index_repository(REPO_ROOT)
    results = retrieve("MRR", chunks, RetrievalConfig(query_intent="explain_metric", max_results=3))
    assert len(results) <= 3


def test_generate_answer_has_content() -> None:
    chunks = index_repository(REPO_ROOT)
    cfg = RetrievalConfig(query_intent="explain_metric")
    results = retrieve("MRR", chunks, cfg)
    answer = generate_answer("MRR", results, mode="extractive", intent="explain_metric")
    assert answer.direct_answer != ""
    assert answer.confidence != ""
    assert answer.citations is not None


def test_answer_unsupported_when_no_evidence() -> None:
    chunks = index_repository(REPO_ROOT)
    cfg = RetrievalConfig(query_intent="find_file", project_filter="nonexistent_project_xyz")
    results = retrieve("xyz_nonexistent_query_12345", chunks, cfg)
    if not results:
        answer = generate_answer("xyz_nonexistent_query_12345", results, mode="extractive", intent="find_file")
        assert answer.unsupported or answer.confidence == "No evidence"


def test_validate_citation_valid() -> None:
    from portfolio.copilot.schema import CopilotCitation
    cit = CopilotCitation(
        file_path="README.md",
        start_line=1,
        end_line=10,
        cell_index=None,
        snippet="test",
        source_type="markdown",
        project_area="root",
    )
    assert validate_citation(cit, REPO_ROOT)


def test_validate_citation_missing_file() -> None:
    from portfolio.copilot.schema import CopilotCitation
    cit = CopilotCitation(
        file_path="nonexistent_file_xyz.md",
        start_line=1,
        end_line=10,
        cell_index=None,
        snippet="test",
        source_type="markdown",
        project_area="root",
    )
    assert not validate_citation(cit, REPO_ROOT)


def test_validate_citations_collapses_duplicates() -> None:
    from portfolio.copilot.schema import CopilotCitation
    cits = [
        CopilotCitation(file_path="README.md", start_line=1, end_line=10, cell_index=None, snippet="a", source_type="markdown", project_area="root"),
        CopilotCitation(file_path="README.md", start_line=20, end_line=30, cell_index=None, snippet="b", source_type="markdown", project_area="root"),
    ]
    result = validate_citations(cits, [], "test")
    assert len(result) <= len(cits)


def test_is_secret_file_env() -> None:
    assert is_secret_file(Path(".env"))


def test_is_secret_file_pem() -> None:
    assert is_secret_file(Path("key.pem"))


def test_is_secret_file_safe() -> None:
    assert not is_secret_file(Path("README.md"))


def test_is_sensitive_content_safe() -> None:
    assert not is_sensitive_content("This is a public README file.")


def test_is_within_repo() -> None:
    assert is_within_repo(REPO_ROOT / "README.md", REPO_ROOT)


def test_conversation_memory_capped() -> None:
    mem = ConversationMemory()
    for i in range(20):
        mem.add("user", f"q{i}")
        mem.add("assistant", f"a{i}")
    assert len(mem.last_n_turns()) <= 12


def test_conversation_memory_entities() -> None:
    mem = ConversationMemory()
    mem.add("user", "MRR nerede hesaplanıyor?", resolved_entity="MRR")
    mem.add("assistant", "MRR is calculated in metrics.py")
    assert "MRR" in mem.resolved_entities()


def test_conversation_memory_clear() -> None:
    mem = ConversationMemory()
    mem.add("user", "test")
    mem.clear()
    assert mem.is_empty()


def test_intent_none_defaults_to_general() -> None:
    assert classify_intent("random gibberish xyz 123") == "general_repository_question"


def test_chunking_preserves_file_references() -> None:
    chunks = index_repository(REPO_ROOT)
    for chunk in chunks:
        if chunk.start_line is not None:
            assert chunk.start_line >= 1
        if chunk.end_line is not None:
            assert chunk.end_line >= chunk.start_line if chunk.start_line is not None else True

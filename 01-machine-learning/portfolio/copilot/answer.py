from __future__ import annotations

from typing import Any

from portfolio.copilot.schema import (
    CopilotAnswer,
    CopilotCitation,
    CopilotChunk,
)
from portfolio.copilot.config import MAX_CITATIONS
from portfolio.copilot.intent import classify_intent
from portfolio.copilot.citation import validate_citations


def _summarize_evidence(chunks: list[CopilotChunk]) -> str:
    if not chunks:
        return "No evidence found in the repository."
    sources = sorted({c.file_path for c in chunks})
    if len(sources) == 1:
        return f"Evidence found in `{sources[0]}`."
    return f"Evidence found across {len(sources)} files: " + ", ".join(f"`{s}`" for s in sources[:5])


def _confidence_from(chunks: list[CopilotChunk], query: str) -> str:
    if not chunks:
        return "No evidence"
    if len(chunks) == 1:
        return "Low — single source"
    if len(chunks) >= 3 and any(c.score >= 0.5 for c in chunks):
        return "High"
    if len(chunks) >= 2 and any(c.score >= 0.3 for c in chunks):
        return "Medium"
    return "Low"


def _build_extractive_answer(query: str, chunks: list[CopilotChunk]) -> str:
    if not chunks:
        return "Bu konuda repoda yeterli doğrulanabilir kanıt bulamadım."

    parts: list[str] = []
    for chunk in chunks[:3]:
        text = chunk.text.strip()
        lines = text.split("\n")
        relevant_lines = [l for l in lines if query.lower() in l.lower() or len(parts) < 3]
        if relevant_lines:
            snippet = "\n".join(relevant_lines[:5])
            if snippet:
                parts.append(snippet)

    if not parts:
        return "Bu konuda repoda yeterli doğrulanabilir kanıt bulamadım."
    return "\n\n".join(parts)


def generate_answer(
    query: str,
    chunks: list[CopilotChunk],
    mode: str = "extractive",
    intent: str | None = None,
) -> CopilotAnswer:
    if intent is None:
        intent = classify_intent(query)

    if mode == "extractive":
        direct = _build_extractive_answer(query, chunks)
    else:
        direct = _build_extractive_answer(query, chunks)

    citations_list = validate_citations(
        citations_for_chunks(chunks), chunks, query
    )

    confidence = _confidence_from(chunks, query)
    unsupported = False

    if confidence == "No evidence":
        direct = "Bu konuda repoda yeterli doğrulanabilir kanıt bulamadım."
        unsupported = True

    return CopilotAnswer(
        direct_answer=direct,
        evidence_summary=_summarize_evidence(chunks),
        citations=citations_list,
        confidence=confidence,
        limitations=None if not unsupported else "Query requires external knowledge not present in repository evidence.",
        intent=intent,
        retrieval_count=len(chunks),
        unsupported=unsupported,
    )


def citations_for_chunks(chunks: list[CopilotChunk]) -> list[CopilotCitation]:
    from portfolio.copilot.retriever import citations_for
    return citations_for(chunks, max_citations=MAX_CITATIONS + 2)
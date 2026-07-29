from __future__ import annotations

from pathlib import Path
from portfolio.copilot.config import REPO_ROOT, ML_ROOT, INDEX_DIR


def render() -> None:
    import streamlit as st
    from portfolio.i18n import t

    st.markdown("# AI Project Copilot")
    st.markdown(
        "**Read-only repository assistant.** Answers questions using "
        "verified repository evidence with inline citations. No code execution, "
        "no persistent memory across users, no external API access."
    )
    st.markdown("""<span style="background:#f0fdf4;color:#15803d;padding:2px 8px;border-radius:4px;font-size:0.8em;">Read-only</span>""", unsafe_allow_html=True)

    col_status, col_index, col_count = st.columns(3)
    with col_status:
        st.markdown("**Status**")
        st.success("Ready")
    with col_index:
        st.markdown("**Repository**")
        st.code(str(REPO_ROOT), language=None)
    with col_count:
        st.markdown("**Indexed Files**")
        st.markdown("See index for count")

    st.divider()

    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []

    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Soru sor (Turkish/English)...")
    if user_input:
        st.session_state.copilot_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            try:
                from portfolio.copilot.indexer import index_repository, load_index, save_index
                from portfolio.copilot.retriever import retrieve, RetrievalConfig
                from portfolio.copilot.answer import generate_answer, classify_intent
                from portfolio.copilot.config import MAX_CITATIONS, MAX_CHUNK_SIZE, COPILOT_DIR

                index_path = INDEX_DIR / "repo_index.json"
                if not index_path.exists() or st.session_state.get("copilot_rebuild_index"):
                    with st.status("Indexing repository...", expanded=True) as status:
                        chunks = index_repository(REPO_ROOT)
                        save_index(chunks, index_path)
                        status.update(label=f"Indexed {len(chunks)} chunks", state="complete")
                else:
                    chunks = load_index(index_path)

                intent = classify_intent(user_input)
                config = RetrievalConfig(query_intent=intent)
                results = retrieve(user_input, chunks, config)

                answer = generate_answer(user_input, results, mode="extractive", intent=intent)

                st.markdown(answer.direct_answer)

                with st.expander("📎 Sources", expanded=False):
                    for cit in answer.citations[:MAX_CITATIONS]:
                        st.markdown(
                            f"- `{cit.file_path}"
                            + (f":{cit.start_line}-{cit.end_line}" if cit.start_line else "")
                            + f"` — score: {cit.retrieval_score:.2f}"
                        )

                if answer.unsupported:
                    st.warning("Bu konudaki soru için repoda doğrulanabilir kanıt bulunamadı.")

                st.session_state.copilot_messages.append({"role": "assistant", "content": answer.direct_answer})

            except Exception as ex:
                st.error(f"Copilot error: {ex}")

    with st.sidebar:
        st.markdown("## Copilot Controls")
        st.selectbox("Language", ["tr", "en"], index=0, key="copilot_lang")
        st.selectbox("Answer Mode", ["extractive"], index=0, key="copilot_mode", help="Generative mode requires external provider configuration")
        st.selectbox("Project Filter", ["All", "search", "churn", "housing", "sentiment", "evaluation", "ml", "root"], index=0, key="copilot_project")
        st.slider("Max Evidence Chunks", 1, 20, 10, key="copilot_max_chunks")
        if st.button("Rebuild Index", key="copilot_rebuild_btn"):
            st.session_state.copilot_rebuild_index = True
            st.rerun()
        if st.button("Clear Conversation", key="copilot_clear_btn"):
            st.session_state.copilot_messages = []
            st.rerun()

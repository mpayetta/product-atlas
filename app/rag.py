import os

from app.vector_store import get_collection, query as vs_query
from app.llm_client import ask_system

SYSTEM_PROMPT = """
You are a senior Product Management copilot.
You answer using ONLY the provided context plus general PM knowledge when needed.
If the context does not contain the answer, say so explicitly.
Be concise but structured, and prefer bullet points when helpful.
"""

RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "8000"))

def build_context(results):
    """
    Turn Chroma query results into a readable context string.
    """
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    parts = []
    for d, m in zip(docs, metas):
        source = m.get("source", "unknown")
        idx = m.get("chunk_index", 0)
        parts.append(f"[Source: {source} (chunk {idx})]\n{d}")

    return "\n\n---\n\n".join(parts)

def rag_answer(user_question: str, k: int = 5) -> str:
    if k is None:
        k = RAG_TOP_K
    """
    Retrieve relevant chunks from pm_docs and ask the LLM to answer.
    """
    coll = get_collection("pm_docs")
    results = vs_query(coll, user_question, k=k)

    # If nothing came back, fail gracefully
    if not results.get("documents") or not results["documents"][0]:
        return "I couldn't find any relevant context in your documents for that question."

    context = build_context(results)
    # optional: truncate context to avoid huge prompts
    context = context[:RAG_MAX_CONTEXT_CHARS]

    prompt = (
        f"Context:\n{context}\n\n"
        f"User question: {user_question}\n\n"
        f"Answer:"
    )

    return ask_system(prompt, SYSTEM_PROMPT)

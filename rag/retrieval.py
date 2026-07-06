from typing import List
from rag.embedding_service import get_provider
from rag.vector_store import search_similar


def retrieve(
    query: str,
    limit: int = 5,
    threshold: float = 0.4,
) -> List[dict]:
    """
    Retrieve chunks paling relevan untuk query tertentu.
    Return: list of {source_file, content, score}
    """
    provider = get_provider()
    query_embedding = provider.embed_single(query)

    results = search_similar(
        query_embedding=query_embedding,
        limit=limit,
        threshold=threshold,
    )

    return [
        {
            "source_file": source,
            "content": content,
            "score": round(score, 4),
        }
        for source, content, score in results
    ]


def format_for_prompt(results: List[dict]) -> str:
    """
    Format hasil retrieval menjadi teks yang siap di-inject ke prompt.
    """
    if not results:
        return ""

    lines = ["Berikut informasi relevan dari knowledge base pribadi:\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] Sumber: {r['source_file']}")
        lines.append(r["content"])
        lines.append("")

    return "\n".join(lines)


def should_use_rag(query: str) -> bool:
    """
    Tentukan apakah query ini butuh knowledge base retrieval.
    Heuristik sederhana — akan diupgrade ke LLM router nanti.
    """
    # Keyword yang mengindikasikan butuh knowledge pribadi
    personal_keywords = [
        "catatan", "note", "dokumentasi", "jarvis", "project",
        "roadmap", "flutter", "backend", "keputusan", "progress",
        "pernah", "sebelumnya", "kemarin", "minggu lalu",
        "apa yang", "gimana", "bagaimana", "explain", "jelaskan",
        "review", "cari", "find", "search", "lookup",
    ]

    query_lower = query.lower()
    return any(kw in query_lower for kw in personal_keywords)
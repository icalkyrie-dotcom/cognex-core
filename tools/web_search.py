import json
import logging
import os

from tavily import TavilyClient

from tools.query_optimizer import optimize_search_query

logger = logging.getLogger(__name__)


def _run_search(client: TavilyClient, query: str, max_results: int):
    """
    Satu kali request ke Tavily.
    """

    logger.info("=" * 70)
    logger.info("🔎 QUERY KE TAVILY")
    logger.info(query)
    logger.info("=" * 70)

    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="basic",
    )

    # DEBUG — hapus setelah selesai investigasi
    import json
    print("=== RAW TAVILY RESPONSE ===")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print("===========================")

    answer = response.get("answer")

    if answer:
        formatted = f"""Jawaban ringkas Tavily:

{answer}

"""
    else:
        formatted = ""

    logger.info("=" * 70)
    logger.info("📄 RESPONSE TAVILY")
    logger.info(json.dumps(response, indent=2)[:4000])
    logger.info("=" * 70)

    return response


def search_web(query: str, max_results: int = 5) -> str:
    """
    Web Search menggunakan Tavily.

    Strategy:

    1. Search original query.
    2. Jika hasil jelek -> retry dengan query yang diperbaiki.
    3. Gunakan AI Answer Tavily bila tersedia.
    """

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return "Web Search tidak tersedia (TAVILY_API_KEY belum diset)."

    client = TavilyClient(api_key=api_key)

    optimized_query = optimize_search_query(query)

    print(f"🔎 Original Query : {query}")
    print(f"✨ Optimized Query: {optimized_query}")

    queries = [
        optimized_query,
        f"{optimized_query} latest",
        f"{optimized_query} official result",
    ]

    best_response = None

    for q in queries:

        response = _run_search(client, q, max_results)

        results = response.get("results", [])

        if results:
            best_response = response
            break

    if not best_response:
        return f"Tidak ditemukan hasil untuk '{query}'."

    answer = best_response.get("answer", "")
    results = best_response.get("results", [])

    output = []

    output.append(f"## Web Search")
    output.append(f"Original Query: {query}")

    formatted = f"Hasil web search untuk '{optimized_query}'\n\n"

    if answer:
        output.append("")
        output.append("### AI Summary")
        output.append(answer)

    output.append("")
    output.append("### Sources")

    for i, r in enumerate(results, 1):

        title = r.get("title", "No title")

        content = (
            r.get("raw_content")
            or r.get("content")
            or ""
        )

        url = r.get("url", "")

        output.append(
            f"""
{i}. {title}

{content[:500]}

Source:
{url}
""".strip()
        )

    return "\n\n".join(output)
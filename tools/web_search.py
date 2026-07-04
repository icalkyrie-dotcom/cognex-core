import os
from tavily import TavilyClient


def search_web(query: str, max_results: int = 3) -> str:
    """
    Melakukan web search menggunakan Tavily.
    Return: string berisi hasil search yang siap di-inject ke prompt.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Web search tidak tersedia: TAVILY_API_KEY tidak ditemukan."

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
        )

        results = response.get("results", [])
        if not results:
            return f"Tidak ada hasil untuk query: {query}"

        formatted = f"Hasil web search untuk '{query}':\n\n"
        for i, r in enumerate(results, 1):
            formatted += f"{i}. **{r.get('title', 'No title')}**\n"
            formatted += f"   {r.get('content', 'No content')[:300]}\n"
            formatted += f"   Source: {r.get('url', '')}\n\n"

        return formatted.strip()

    except Exception as e:
        return f"Web search gagal: {str(e)}"
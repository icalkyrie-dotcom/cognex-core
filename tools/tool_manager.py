from tools.web_search import search_web
from tools.url_reader import read_url

TOOLS = {
    "web_search": {
        "fn": search_web,
        "description": "Search informasi terbaru dari internet.",
        "params": ["query"],
    },
    "read_url": {
        "fn": read_url,
        "description": (
            "Membaca dan mengekstrak konten dari URL tertentu. "
            "Gunakan ketika user memberikan link spesifik yang ingin dibaca."
        ),
        "params": ["url"],
    },
}


def get_tool_definitions() -> list[dict]:
    return [
        {
            "name": name,
            "description": tool["description"],
            "params": tool["params"],
        }
        for name, tool in TOOLS.items()
    ]


def execute_tool(tool_name: str, params: dict) -> str:
    if tool_name not in TOOLS:
        return f"Tool '{tool_name}' tidak ditemukan."
    try:
        return TOOLS[tool_name]["fn"](**params)
    except Exception as e:
        return f"Tool execution failed: {str(e)}"
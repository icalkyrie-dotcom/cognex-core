from llm.llm import generate_response


def optimize_search_query(user_query: str) -> str:
    """
    Mengubah query user menjadi query search yang lebih spesifik.
    """

    system = """
Kamu adalah Search Query Optimizer.

Tugasmu adalah mengubah pertanyaan user menjadi query web search
yang paling efektif.

Aturan:

- Jangan mengubah maksud user.
- Tambahkan konteks jika diperlukan.
- Untuk olahraga:
  - tambahkan nama kompetisi jika bisa disimpulkan
  - gunakan bahasa Inggris
  - tambahkan kata:
    result
    score
    latest
    today
    match

- Untuk teknologi:
  tambahkan:
    latest news

- Untuk perusahaan:
  tambahkan:
    latest update

Balas HANYA dengan query.
Tanpa tanda kutip.
Tanpa penjelasan.
"""

    try:
        result = generate_response(
            [{"role": "user", "content": user_query}],
            system=system
        )

        return result.strip()

    except Exception:
        return user_query
from rag.retrieval import retrieve, format_for_prompt

queries = [
    "Apa stack yang dipakai di project Jarvis?",
    "Ceritakan tentang phase yang sudah selesai",
    "Apa keputusan teknis terkait database?",
    "Flutter packages apa yang dipakai?",
]

for query in queries:
    print(f"\n{'='*50}")
    print(f"Query: {query}")
    print(f"{'='*50}")

    results = retrieve(query, limit=3, threshold=0.3)

    if not results:
        print("❌ Tidak ada hasil relevan")
        continue

    for r in results:
        print(f"\n📄 {r['source_file']} (score: {r['score']})")
        print(f"   {r['content'][:150]}...")

    print(f"\n--- Formatted for prompt ---")
    print(format_for_prompt(results)[:300])
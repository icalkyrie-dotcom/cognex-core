from rag.ingest import ingest_directory
from rag.vector_store import list_indexed_files

print("=== TEST INGEST DIRECTORY ===\n")
summary = ingest_directory("knowledge")
print(f"\nSummary: {summary}")

print("\n=== INDEXED FILES ===")
files = list_indexed_files()
for f in files:
    print(f"  - {f}")
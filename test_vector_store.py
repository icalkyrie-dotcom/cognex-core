from rag.vector_store import list_indexed_files, engine
from sqlalchemy import text

print("Testing Supabase connection...")

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM knowledge_chunks"))
    count = result.scalar()
    print(f"✅ Connected to Supabase")
    print(f"   knowledge_chunks rows: {count}")

files = list_indexed_files()
print(f"   Indexed files: {files}")
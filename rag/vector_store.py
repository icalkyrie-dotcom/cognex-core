import uuid
from typing import List, Tuple
from sqlalchemy import create_engine, text
from config import VECTOR_DATABASE_URL


engine = create_engine(VECTOR_DATABASE_URL)


def save_chunks(
    source_file: str,
    chunks: List[str],
    embeddings: List[List[float]]
) -> int:
    """Simpan chunks dan embeddings ke Supabase. Return jumlah chunk tersimpan."""
    saved = 0
    with engine.connect() as conn:
        # Hapus chunks lama dari file yang sama (re-ingest)
        conn.execute(
            text("DELETE FROM knowledge_chunks WHERE source_file = :src"),
            {"src": source_file}
        )

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            conn.execute(
                text("""
                    INSERT INTO knowledge_chunks
                    (id, source_file, chunk_index, content, embedding)
                    VALUES (:id, :src, :idx, :content, :embedding)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "src": source_file,
                    "idx": i,
                    "content": chunk,
                    "embedding": str(embedding),
                }
            )
            saved += 1

        conn.commit()
    return saved


def search_similar(
    query_embedding: List[float],
    limit: int = 5,
    threshold: float = 0.7
) -> List[Tuple[str, str, float]]:
    """
    Cari chunks paling relevan berdasarkan cosine similarity.
    Return: list of (source_file, content, similarity_score)
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT
                    source_file,
                    content,
                    1 - (embedding <=> :query_embedding) AS similarity
                FROM knowledge_chunks
                WHERE 1 - (embedding <=> :query_embedding) > :threshold
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
            """),
            {
                "query_embedding": str(query_embedding),
                "threshold": threshold,
                "limit": limit,
            }
        )
        return [(row[0], row[1], row[2]) for row in result]


def list_indexed_files() -> List[str]:
    """Return list semua file yang sudah di-index."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT DISTINCT source_file FROM knowledge_chunks ORDER BY source_file")
        )
        return [row[0] for row in result]


def delete_file_chunks(source_file: str) -> int:
    """Hapus semua chunks dari file tertentu. Return jumlah yang dihapus."""
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM knowledge_chunks WHERE source_file = :src RETURNING id"),
            {"src": source_file}
        )
        count = result.rowcount
        conn.commit()
    return count
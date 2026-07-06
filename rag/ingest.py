import os
from pathlib import Path
from typing import List
from rag.embedding_service import get_provider
from rag.vector_store import save_chunks


def chunk_markdown(content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split markdown content menjadi chunks.
    Prioritas split: per heading, lalu per paragraf, lalu per karakter.
    """
    chunks = []

    # Split per heading dulu
    import re
    sections = re.split(r'\n(?=#{1,3} )', content)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        if len(section) <= chunk_size:
            chunks.append(section)
        else:
            # Section terlalu panjang, split per paragraf
            paragraphs = section.split("\n\n")
            current = ""

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                if len(current) + len(para) <= chunk_size:
                    current = (current + "\n\n" + para).strip()
                else:
                    if current:
                        chunks.append(current)
                    # Kalau paragraf sendiri masih terlalu panjang
                    if len(para) > chunk_size:
                        for i in range(0, len(para), chunk_size - overlap):
                            chunks.append(para[i:i + chunk_size])
                    else:
                        current = para

            if current:
                chunks.append(current)

    return [c for c in chunks if len(c.strip()) > 20]


def ingest_file(file_path: str) -> dict:
    """
    Ingest satu file Markdown ke vector store.
    Return: dict dengan info hasil ingest.
    """
    path = Path(file_path)
    if not path.exists():
        return {"success": False, "error": f"File tidak ditemukan: {file_path}"}

    if not path.suffix == ".md":
        return {"success": False, "error": f"Bukan file Markdown: {file_path}"}

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return {"success": False, "error": f"File kosong: {file_path}"}

    # Chunking
    chunks = chunk_markdown(content)
    if not chunks:
        return {"success": False, "error": "Tidak ada chunk yang dihasilkan"}

    print(f"📄 {path.name}: {len(chunks)} chunks")

    # Embedding
    provider = get_provider()
    embeddings = provider.embed(chunks)

    print(f"🔢 Embedding selesai: {len(embeddings)} vectors")

    # Save ke vector store
    source_file = path.name
    saved = save_chunks(source_file, chunks, embeddings)

    print(f"💾 Tersimpan: {saved} chunks → Supabase")

    return {
        "success": True,
        "file": source_file,
        "chunks": len(chunks),
        "saved": saved,
    }


def ingest_directory(directory: str = "knowledge") -> dict:
    """
    Ingest semua file Markdown dari folder knowledge/.
    Return: summary hasil ingest.
    """
    knowledge_dir = Path(directory)
    if not knowledge_dir.exists():
        return {"success": False, "error": f"Folder tidak ditemukan: {directory}"}

    md_files = list(knowledge_dir.glob("*.md"))
    if not md_files:
        return {"success": False, "error": "Tidak ada file .md di folder knowledge/"}

    print(f"\n🚀 Memulai ingest {len(md_files)} file...\n")

    results = []
    for md_file in md_files:
        result = ingest_file(str(md_file))
        results.append(result)
        print()

    success = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    summary = {
        "total_files": len(md_files),
        "success": len(success),
        "failed": len(failed),
        "total_chunks": sum(r.get("chunks", 0) for r in success),
        "errors": [r.get("error") for r in failed],
    }

    print(f"✅ Selesai: {summary['success']}/{summary['total_files']} file")
    print(f"   Total chunks: {summary['total_chunks']}")
    if failed:
        print(f"   Failed: {summary['errors']}")

    return summary
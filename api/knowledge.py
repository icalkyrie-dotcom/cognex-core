from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path
import shutil

from db.database import get_db
from rag.ingest import ingest_file, ingest_directory
from rag.vector_store import list_indexed_files, delete_file_chunks
from config import APP_SECRET_KEY

router = APIRouter()
KNOWLEDGE_DIR = Path("knowledge")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != APP_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.get("/knowledge/files")
def list_files(_: None = Depends(verify_api_key)):
    """List semua file yang sudah di-index di knowledge base."""
    files = list_indexed_files()
    return {"files": files, "count": len(files)}


@router.post("/knowledge/ingest/all")
def ingest_all(_: None = Depends(verify_api_key)):
    """Re-ingest semua file di folder knowledge/."""
    result = ingest_directory(str(KNOWLEDGE_DIR))
    if not result.get("success", True) and result.get("total_files", 0) == 0:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.post("/knowledge/ingest/file")
def ingest_single_file(
    filename: str,
    _: None = Depends(verify_api_key),
):
    """Ingest satu file spesifik dari folder knowledge/."""
    file_path = KNOWLEDGE_DIR / filename
    result = ingest_file(str(file_path))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/knowledge/upload")
async def upload_and_ingest(
    file: UploadFile = File(...),
    _: None = Depends(verify_api_key),
):
    """Upload file Markdown baru dan langsung ingest."""
    if not file.filename.endswith(".md"):
        raise HTTPException(
            status_code=400,
            detail="Hanya file .md yang diizinkan"
        )

    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    save_path = KNOWLEDGE_DIR / file.filename

    with save_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    result = ingest_file(str(save_path))
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    return result


@router.delete("/knowledge/files/{filename}")
def delete_file(
    filename: str,
    _: None = Depends(verify_api_key),
):
    """Hapus file dari knowledge base (vector store saja, file tetap ada)."""
    count = delete_file_chunks(filename)
    if count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' tidak ditemukan di knowledge base"
        )
    return {"deleted": filename, "chunks_removed": count}
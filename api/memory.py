from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import (
    get_db,
    set_memory,
    get_memory,
    get_all_memories,
    Memory,
)

from config import APP_SECRET_KEY

router = APIRouter()


class MemoryRequest(BaseModel):
    key: str
    value: str


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != APP_SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )


@router.post("/memory")
def save_memory_endpoint(
    request: MemoryRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    mem = set_memory(db, request.key, request.value)

    return {
        "key": mem.key,
        "value": mem.value,
    }


@router.get("/memory")
def get_all_memories_endpoint(
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    memories = get_all_memories(db)

    return {
        "memories": [
            {
                "key": m.key,
                "value": m.value,
            }
            for m in memories
        ]
    }


@router.get("/memory/{key}")
def get_memory_endpoint(
    key: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    mem = get_memory(db, key)

    if not mem:
        raise HTTPException(
            status_code=404,
            detail="Memory not found",
        )

    return {
        "key": mem.key,
        "value": mem.value,
    }


@router.delete("/memory/{key}")
def delete_memory_endpoint(
    key: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    mem = db.query(Memory).filter(
        Memory.key == key
    ).first()

    if not mem:
        raise HTTPException(
            status_code=404,
            detail="Memory not found",
        )

    db.delete(mem)
    db.commit()

    return {
        "deleted": key,
    }
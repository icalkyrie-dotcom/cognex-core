from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import (
    get_db,
    create_conversation,
    get_conversation,
    get_all_conversations,
    get_messages,
)
from config import APP_SECRET_KEY

router = APIRouter()


class UpdateTitleRequest(BaseModel):
    title: str


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != APP_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    conversations = get_all_conversations(db)
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in conversations
        ]
    }


@router.get("/conversations/{conversation_id}")
def get_conversation_detail(
    conversation_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    conv = get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = get_messages(db, conversation_id, limit=100)
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.patch("/conversations/{conversation_id}/title")
def update_title(
    conversation_id: str,
    request: UpdateTitleRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    conv = get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.title = request.title
    db.commit()
    return {"id": conv.id, "title": conv.title}


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    conv = get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conv)
    db.commit()
    return {"deleted": conversation_id}
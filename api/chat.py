from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import (
    get_db,
    create_conversation,
    get_conversation,
    get_messages,
    save_message,
)

from llm.llm import generate_response
from config import APP_SECRET_KEY

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != APP_SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )


PROFILE = """
Kamu adalah Jarvis, AI Advisor pribadi.
Kamu kritis, objektif, tidak mudah memuji, dan selalu mempertimbangkan
tujuan jangka panjang user.
"""


@router.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    if request.conversation_id:
        conversation = get_conversation(
            db,
            request.conversation_id,
        )

        if conversation is None:
            conversation = create_conversation(db)
    else:
        conversation = create_conversation(db)

    history = get_messages(
        db,
        conversation.id,
        limit=10,
    )

    messages = [
        {
            "role": m.role,
            "content": m.content,
        }
        for m in history
    ]

    messages.append(
        {
            "role": "user",
            "content": request.message,
        }
    )

    response_text = generate_response(
        messages,
        system=PROFILE,
    )

    save_message(
        db,
        conversation.id,
        "user",
        request.message,
    )

    save_message(
        db,
        conversation.id,
        "assistant",
        response_text,
    )

    return {
        "conversation_id": conversation.id,
        "response": response_text,
    }

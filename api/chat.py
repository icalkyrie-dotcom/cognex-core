from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db, save_message, get_recent_messages
from llm.llm import generate_response
from config import APP_SECRET_KEY

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != APP_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


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
    history = get_recent_messages(db, limit=10)
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": request.message})

    response_text = generate_response(messages, system=PROFILE)

    save_message(db, "user", request.message)
    save_message(db, "assistant", response_text)

    return {"response": response_text}
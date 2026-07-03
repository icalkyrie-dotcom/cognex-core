from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import (
    get_db,
    create_conversation,
    get_conversation,
    get_messages,
    save_message,
    get_all_memories,
)
from llm.llm import generate_response
from config import APP_SECRET_KEY

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != APP_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


BASE_PROFILE = """
Kamu adalah Jarvis, AI Advisor pribadi.
Kamu kritis, objektif, tidak mudah memuji, dan selalu mempertimbangkan
tujuan jangka panjang user.
"""


def build_system_prompt(db: Session) -> str:
    memories = get_all_memories(db)
    if not memories:
        return BASE_PROFILE

    memory_text = "\n".join([f"- {m.key}: {m.value}" for m in memories])
    return f"""{BASE_PROFILE}

Berikut adalah informasi penting tentang user yang harus selalu kamu ingat:
{memory_text}

Gunakan informasi ini untuk memberikan jawaban yang personal dan relevan.
"""


def generate_title(message: str) -> str:
    prompt = [{"role": "user", "content": message}]
    system = (
        "Buat judul singkat (maksimal 5 kata) dalam Bahasa Indonesia "
        "yang merangkum topik pesan berikut. "
        "Balas hanya dengan judul, tanpa tanda kutip, tanpa penjelasan tambahan."
    )
    try:
        title = generate_response(prompt, system=system)
        return title.strip()[:100]
    except Exception:
        return "New Chat"


@router.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    is_new_conversation = False

    if request.conversation_id:
        conversation = get_conversation(db, request.conversation_id)
        if conversation is None:
            conversation = create_conversation(db)
            is_new_conversation = True
    else:
        conversation = create_conversation(db)
        is_new_conversation = True

    # Auto-generate title dari pesan pertama
    if is_new_conversation:
        title = generate_title(request.message)
        conversation.title = title
        db.commit()

    history = get_messages(db, conversation.id, limit=10)
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": request.message})

    system_prompt = build_system_prompt(db)
    response_text = generate_response(messages, system=system_prompt)

    save_message(db, conversation.id, "user", request.message)
    save_message(db, conversation.id, "assistant", response_text)

    return {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "response": response_text,
    }
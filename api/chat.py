from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from db.database import (
    get_db,
    create_conversation,
    get_conversation,
    get_messages,
    save_message,
    get_all_memories,
    set_memory,
)
from llm.llm import generate_response
from core.context_builder import build_context
from config import APP_SECRET_KEY

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != APP_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def build_system_prompt(db: Session) -> str:
    memories = get_all_memories(db)
    return build_context(memories=memories)


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


def extract_and_save_facts(db: Session, user_message: str):
    prompt = [{"role": "user", "content": user_message}]
    system = """Tugasmu adalah mengekstrak fakta penting tentang user dari pesan berikut.

Fakta yang layak disimpan (fact-worthy):
- Nama user
- Pekerjaan atau profesi
- Tujuan karier atau hidup
- Skill atau teknologi yang sedang dipelajari
- Project yang sedang dikerjakan
- Preferensi atau kebiasaan penting
- Informasi personal yang relevan jangka panjang

Yang TIDAK perlu disimpan:
- Pertanyaan biasa
- Fakta umum yang bukan tentang user
- Informasi yang terlalu spesifik atau tidak relevan jangka panjang

Format respons (JSON array, kosong jika tidak ada fakta):
[
  {"key": "nama", "value": "Budi"},
  {"key": "pekerjaan", "value": "Backend Engineer"}
]

Jika tidak ada fakta yang layak disimpan, balas dengan array kosong: []
Balas HANYA dengan JSON. Tidak ada teks lain."""

    try:
        result = generate_response(prompt, system=system)
        result = result.strip()

        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])

        facts = json.loads(result)

        if not isinstance(facts, list):
            return

        for fact in facts:
            if isinstance(fact, dict) and "key" in fact and "value" in fact:
                key = str(fact["key"]).strip().lower().replace(" ", "_")
                value = str(fact["value"]).strip()
                if key and value:
                    set_memory(db, key, value)
                    print(f"💾 Saved memory: {key} = {value}")

    except Exception as e:
        print(f"⚠️ Memory extraction failed: {e}")


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

    extract_and_save_facts(db, request.message)

    return {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "response": response_text,
    }
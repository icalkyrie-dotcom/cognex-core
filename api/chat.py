from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import re

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
from tools.tool_manager import get_tool_definitions, execute_tool
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
        "Balas hanya dengan judul, tanpa tanda kutip, "
        "tanpa penjelasan tambahan."
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

Jika tidak ada fakta, balas: []
Balas HANYA dengan JSON."""

    try:
        result = generate_response(prompt, system=system)
        result = result.strip()

        # Bersihkan semua variasi markdown code block
        result = re.sub(r"```(?:json)?\s*", "", result)
        result = re.sub(r"```", "", result)

        # Ambil hanya bagian JSON array, buang teks sebelum/sesudahnya
        match = re.search(r"\[.*?\]", result, re.DOTALL)
        if not match:
            return
        result = match.group(0)

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


def should_use_tool(message: str, tool_definitions: list) -> dict | None:
    """
    Tanya LLM apakah pesan ini butuh tool.
    Return dict {tool_name, params} atau None.
    """
    tools_text = json.dumps(tool_definitions, ensure_ascii=False, indent=2)

    system = f"""Kamu adalah router yang memutuskan apakah sebuah pertanyaan membutuhkan tool eksternal.

Tools yang tersedia:
{tools_text}

Aturan:
- Gunakan web_search HANYA jika pertanyaan butuh informasi terbaru, 
  berita, harga, atau data real-time yang tidak mungkin kamu ketahui.
- Jangan gunakan tool untuk pertanyaan umum, opini, atau analisis 
  yang bisa dijawab dari knowledge sendiri.
- Jangan gunakan tool untuk pertanyaan tentang user atau percakapan sebelumnya.

Jika butuh tool, balas dengan JSON:
{{"tool": "web_search", "params": {{"query": "search query yang tepat"}}}}

Jika tidak butuh tool, balas dengan:
{{"tool": null}}

Balas HANYA dengan JSON. Tidak ada teks lain."""

    try:
        result = generate_response(
            [{"role": "user", "content": message}],
            system=system
        )
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])

        decision = json.loads(result)
        if decision.get("tool"):
            print(f"🔧 Tool selected: {decision['tool']}")
            return decision
        return None

    except Exception as e:
        print(f"⚠️ Tool routing failed: {e}")
        return None


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

    # Tool calling check
    tool_used = None
    tool_definitions = get_tool_definitions()
    tool_decision = should_use_tool(request.message, tool_definitions)

    if tool_decision and tool_decision.get("tool"):
        tool_name = tool_decision["tool"]
        tool_params = tool_decision.get("params", {})
        tool_result = execute_tool(tool_name, tool_params)
        tool_used = tool_name
        print(f"🔍 Tool result preview: {tool_result[:100]}...")

        # Inject tool result ke messages
        messages.append({
            "role": "user",
            "content": (
                f"[Tool Result - {tool_name}]\n{tool_result}\n\n"
                f"Gunakan informasi di atas untuk menjawab pertanyaan: "
                f"{request.message}"
            )
        })

    response_text = generate_response(messages, system=system_prompt)

    save_message(db, conversation.id, "user", request.message)
    save_message(db, conversation.id, "assistant", response_text)

    extract_and_save_facts(db, request.message)

    return {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "response": response_text,
        "tool_used": tool_used,
    }
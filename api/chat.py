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
from rag.retrieval import retrieve, format_for_prompt, should_use_rag
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


def should_use_tool(
    message: str,
    tool_definitions: list,
    history: list | None = None,
) -> dict | None:
    """
    Tanya LLM apakah pesan ini butuh tool.
    Return dict {tool_name, params} atau None.
    """
    tools_text = json.dumps(tool_definitions, ensure_ascii=False, indent=2)

    history_text = ""
    if history:
        recent = history[-4:]
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content'][:200]}"
            for m in recent
        )

    history_section = ""
    if history_text:
        history_section = f"""
Konteks percakapan sebelumnya:
{history_text}
"""

    system = f"""Kamu adalah router yang memutuskan apakah pertanyaan membutuhkan tool eksternal.

Tools yang tersedia:
{tools_text}

{history_section}

Aturan:
- Gunakan web_search jika pertanyaan membutuhkan informasi terbaru.
- Gunakan web_search jika pertanyaan adalah follow-up dari topik yang sebelumnya membutuhkan web search.
- Gunakan read_url jika user memberi URL.
- Jangan gunakan tool untuk pertanyaan tentang user atau knowledge pribadi.

Balas HANYA JSON.

Jika perlu:
{{"tool":"web_search","params":{{"query":"..."}}}}

Jika tidak:
{{"tool":null}}
"""

    try:
        result = generate_response(
            [{"role": "user", "content": message}],
            system=system
        )
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])

        print("\n========== ROUTER DEBUG ==========")
        print("MESSAGE:")
        print(message)

        print("\nHISTORY:")
        print(history_text if history_text else "(EMPTY)")

        print("\nRAW LLM OUTPUT:")
        print(result)

        print("==================================\n")

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

    # RAG retrieval
    rag_context = ""
    try:
        if should_use_rag(request.message):
            rag_results = retrieve(request.message, limit=3, threshold=0.3)
            if rag_results:
                rag_context = format_for_prompt(rag_results)
                print(f"📚 RAG: {len(rag_results)} chunks retrieved")
            else:
                print("📚 RAG: no relevant chunks found")
    except Exception as e:
        print(f"⚠️ RAG retrieval failed: {e}")

    # Tool calling check
    tool_used = None
    tool_definitions = get_tool_definitions()
    tool_decision = should_use_tool(
        request.message,
        tool_definitions,
        messages[:-1],
    )

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
                f"[TOOL RESULT]\n"
                f"{tool_result}\n\n"

                "PENTING:\n"
                "- Jawab HANYA berdasarkan TOOL RESULT di atas.\n"
                "- Jangan menggunakan pengetahuan internal jika bertentangan.\n"
                "- Jangan mengarang nama pemain, skor, assist, atau statistik.\n"
                "- Jika informasi tidak ada pada TOOL RESULT, katakan dengan jelas bahwa informasi tersebut tidak tersedia.\n\n"

                f"Pertanyaan pengguna:\n{request.message}"
            )
        })

    final_system = system_prompt
    if rag_context:
        final_system = system_prompt + f"\n\n---\n\n{rag_context}"

    response_text = generate_response(messages, system=final_system)

    save_message(db, conversation.id, "user", request.message)
    save_message(db, conversation.id, "assistant", response_text)

    extract_and_save_facts(db, request.message)

    return {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "response": response_text,
        "tool_used": tool_used,
        "rag_used": bool(rag_context),
    }
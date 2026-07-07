# 🤖 Jarvis AI Assistant

> An AI Assistant built with **FastAPI**, **Flutter**, **Groq**, **Supabase pgvector**, **RAG**, and **Tool Calling**.

Jarvis is a personal AI assistant designed to provide intelligent conversations with long-term memory, Retrieval-Augmented Generation (RAG), knowledge management, and real-time web search.

---

# 📱 Demo

> *(Screenshots & GIF will be added soon)*

| Home | Conversation |
|------|--------------|
| Coming Soon | Coming Soon |

| Sidebar | Voice Mode |
|---------|------------|
| Coming Soon | Coming Soon |

---

# ✨ Features

## 💬 AI Chat

- Multi-conversation support
- Conversation title generation
- Context-aware responses
- Conversation history

---

## 🧠 Long-Term Memory

- Automatic memory extraction
- User preference storage
- Persistent memories
- Memory-aware conversations

Example:

User:

> I'm a Backend Engineer.

Later...

User:

> What do you know about me?

Jarvis already remembers.

---

## 📚 Knowledge Base (RAG)

Upload your own documents and let Jarvis answer based on them.

Current pipeline:

Document

↓

Embedding

↓

Supabase pgvector

↓

Semantic Retrieval

↓

LLM

Supported:

- PDF
- Markdown
- TXT

---

## 🌍 Tool Calling

Jarvis can automatically decide when external tools are required.

Current tools:

- ✅ Web Search (Tavily)
- ✅ URL Reader
- ✅ Knowledge Retrieval

Tool routing is handled automatically by the LLM.

---

## 🔎 Web Search

Jarvis performs web searches for:

- Latest news
- Sports results
- Real-time information
- Current events

The assistant automatically decides whether a question requires internet access.

---

## 🧩 Context-Aware Tool Routing

Jarvis understands follow-up questions.

Example:

User:

> Portugal vs Spain today

↓

User:

> Who scored?

Instead of treating the second message independently, Jarvis uses previous conversation context to determine the correct search query.

---

## 🧠 Prompt Injection Protection

When external tool results are available, Jarvis is instructed to:

- Never fabricate information
- Never mix stale model knowledge
- Only answer using retrieved tool results
- Clearly state when information is unavailable

---

# 🏗 Architecture

```
Flutter App
      │
      ▼
 FastAPI Backend
      │
 ├───────────────┐
 │               │
 ▼               ▼
Memory         Tool Router
 │               │
 ▼               ▼
PostgreSQL    Tavily Search
 │               │
 └──────┬────────┘
        ▼
  RAG Retrieval
        │
        ▼
 Supabase pgvector
        │
        ▼
     Groq LLM
```

---

# ⚙ Tech Stack

| Layer | Technology |
|---------|------------|
| Frontend | Flutter |
| Backend | FastAPI |
| LLM | Groq |
| Embeddings | Sentence Transformers |
| Vector Database | Supabase pgvector |
| Database | PostgreSQL |
| Search | Tavily |
| Deployment | Railway |
| ORM | SQLAlchemy |

---

# 🚀 Getting Started

## Clone

```bash
git clone https://github.com/YOUR_USERNAME/jarvis.git

cd jarvis
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create:

```
.env
```

Example:

```env
GROQ_API_KEY=

TAVILY_API_KEY=

VECTOR_DATABASE_URL=

APP_SECRET_KEY=
```

---

## Run

```bash
uvicorn main:app --reload
```

Server:

```
http://127.0.0.1:8000
```

---

# 📡 API

Main endpoint:

```
POST /chat
```

Knowledge API:

```
POST /knowledge/upload

POST /knowledge/ingest/all

GET /knowledge/files

DELETE /knowledge/files/{filename}
```

Complete API documentation:

➡ **docs/API.md**

---

# 📂 Project Structure

```
Jarvis/

backend/

flutter/

docs/

README.md

requirements.txt

.env.example
```

---

# 📖 Documentation

Detailed documentation is available inside the **docs** folder.

| Document | Description |
|-----------|-------------|
| 📘 docs/Architecture.md | Overall system architecture |
| 📘 docs/API.md | REST API documentation |
| 📘 docs/Backend.md | Backend implementation |
| 📘 docs/Flutter.md | Flutter application |
| 📘 docs/Roadmap.md | Development roadmap |
| 📘 docs/Changelog.md | Project progress |
| 📘 docs/Decisions.md | Technical decisions |
| 📘 docs/Limitations.md | Current limitations |

---

# 🛣 Development Roadmap

## ✅ Phase 1

- Basic Chat
- Groq Integration
- Multi Conversation

---

## ✅ Phase 2

- Memory System
- Persistent Memory
- Sidebar
- Conversation History

---

## ✅ Phase 3

- Knowledge Base
- RAG
- Supabase pgvector
- Embeddings
- Semantic Search

---

## ✅ Phase 4

- Tool Calling
- Tavily Web Search
- URL Reader
- Knowledge API
- Context-aware Tool Routing
- Prompt Injection Protection

---

## 🚧 Phase 5

Planned:

- Conversation Summarization
- Long-term Knowledge Generation
- Reminder System
- Task Planning
- Background Jobs
- Multi-Agent Workflow

---

# ⚠ Current Limitations

Current implementation intentionally prioritizes **reliability over hallucination**.

Known limitations:

- Web search currently relies on Tavily Free.
- Some sports statistics (goal scorer, assists, lineups, player ratings) may not always be available if the search provider only returns short snippets.
- Jarvis will refuse to invent missing information and instead explicitly state that the information is unavailable.

Planned improvements:

- Hybrid Web Search (Search + URL Reader)
- Claude / Gemini powered Query Rewriting
- Better follow-up search refinement
- Multi-source search aggregation

---

# 📈 Current Status

Current Phase:

> ✅ Phase 4 Complete

Backend Status:

✅ Stable

Production:

✅ Railway

Knowledge Base:

✅ Working

Memory:

✅ Working

RAG:

✅ Working

Tool Calling:

✅ Working

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

Feel free to open an Issue or submit a Pull Request.

---

# 📄 License

MIT License

---

Made with ❤️ using FastAPI, Flutter, Groq, Supabase, and a lot of coffee ☕

# Project Jarvis

## Overview

Jarvis adalah Personal AI Operating System yang saya bangun sebagai AI Assistant utama untuk menggantikan ChatGPT dalam pekerjaan sehari-hari.

Targetnya bukan sekadar chatbot, tetapi AI yang memiliki memory jangka panjang, knowledge pribadi, mampu menggunakan tools, dan memahami seluruh project yang sedang saya kerjakan.

---

## Owner

Nama: Faisal Atmaja (Kycal)

---

## Tech Stack

### Mobile
- Flutter

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL (Railway)

### Knowledge Base
- Supabase
- pgvector
- sentence-transformers all-MiniLM-L6-v2

### AI
- Groq API
- Tavily Search

---

## Fitur yang sudah selesai

### Phase 1
- Backend FastAPI
- Flutter App
- Voice Input
- Voice Output
- Gesture Launch

### Phase 2
- Conversation History
- Global Memory
- Memory Extraction
- Static Context

### Phase 3
- Tool Calling
- Tavily Web Search
- URL Reader
- Flutter Tool Indicator
- Production Deployment

---

## Phase 4

Membangun Knowledge Base menggunakan RAG.

Pipeline:

Markdown
→ Chunking
→ Embedding
→ pgvector (Supabase)
→ Similarity Search
→ Context Injection ke LLM

---

## Long Term Vision

Jarvis akan menjadi AI Assistant utama untuk seluruh aktivitas saya.

Kemampuan akhirnya meliputi:

- Memory permanen
- Knowledge pribadi
- Membaca dokumentasi project
- Membantu coding
- Membantu bisnis
- Menjadi pengganti utama ChatGPT

---

## Keputusan Arsitektur

- Database utama menggunakan PostgreSQL Railway.
- Vector database menggunakan Supabase pgvector.
- Embedding menggunakan sentence-transformers dengan abstraction layer sehingga bisa diganti ke OpenAI tanpa mengubah pipeline.
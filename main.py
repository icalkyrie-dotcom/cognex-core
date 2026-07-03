from fastapi import FastAPI
from api.chat import router as chat_router
from api.memory import router as memory_router
from api.conversation import router as conversation_router
from db.database import init_db

app = FastAPI(
    title="Jarvis Backend"
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(conversation_router)

@app.get("/")
def root():
    return {
        "status": "Jarvis is running"
    }


@app.get("/")
def root():
    return {"status": "Jarvis is running"}
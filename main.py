from fastapi import FastAPI
from api.chat import router as chat_router

app = FastAPI(title="Jarvis Backend")

app.include_router(chat_router)


@app.get("/")
def root():
    return {"status": "Jarvis is running"}
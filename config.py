import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./jarvis.db"
)
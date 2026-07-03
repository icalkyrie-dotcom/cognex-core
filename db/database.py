from sqlalchemy import (
    create_engine, Column, String,
    Text, DateTime, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ─── Models ──────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True,
                default=lambda: str(uuid.uuid4()))
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation",
                            cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True,
                default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String,
                             ForeignKey("conversations.id"),
                             nullable=False)
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation",
                                back_populates="messages")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True,
                default=lambda: str(uuid.uuid4()))
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


# ─── Init DB ─────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)


# ─── Session ─────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Conversation Helpers ─────────────────────────────────

def create_conversation(db, title: str = "New Chat") -> Conversation:
    conv = Conversation(title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation(db, conversation_id: str):
    return db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()


def get_all_conversations(db):
    return db.query(Conversation).order_by(
        Conversation.updated_at.desc()
    ).all()


# ─── Message Helpers ──────────────────────────────────────

def save_message(db, conversation_id: str,
                 role: str, content: str) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(msg)
    db.commit()
    return msg


def get_messages(db, conversation_id: str,
                 limit: int = 10) -> list[Message]:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))


# ─── Memory Helpers ───────────────────────────────────────

def set_memory(db, key: str, value: str) -> Memory:
    mem = db.query(Memory).filter(Memory.key == key).first()
    if mem:
        mem.value = value
        mem.updated_at = datetime.utcnow()
    else:
        mem = Memory(key=key, value=value)
        db.add(mem)
    db.commit()
    return mem


def get_memory(db, key: str):
    return db.query(Memory).filter(Memory.key == key).first()


def get_all_memories(db) -> list[Memory]:
    return db.query(Memory).all()
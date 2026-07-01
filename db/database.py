from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_message(db, role: str, content: str):
    msg = Message(role=role, content=content)
    db.add(msg)
    db.commit()
    return msg


def get_recent_messages(db, limit: int = 10):
    messages = (
        db.query(Message)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))
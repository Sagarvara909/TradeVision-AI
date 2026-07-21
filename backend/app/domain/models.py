import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, ForeignKey, DateTime, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploaded_images = relationship("UploadedImage", back_populates="user")
    reports = relationship("Report", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    settings = relationship("Settings", back_populates="user", uselist=False)


class UploadedImage(Base):
    __tablename__ = "uploaded_images"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    ocr_status = Column(String, default="pending")
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="uploaded_images")
    report = relationship("Report", back_populates="image", uselist=False)


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    image_id = Column(UUID(as_uuid=False), ForeignKey("uploaded_images.id"), nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    confidence_score = Column(Float)
    indicators = Column(JSON)
    llm_report = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")
    image = relationship("UploadedImage", back_populates="report")
    history_entries = relationship("AnalysisHistory", back_populates="report")
    chat_messages = relationship("ChatMessage", back_populates="report")


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    report_id = Column(UUID(as_uuid=False), ForeignKey("reports.id"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="history_entries")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    report_id = Column(UUID(as_uuid=False), ForeignKey("reports.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="chat_messages")


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlists")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)
    theme = Column(String, default="dark")
    default_exchange = Column(String, nullable=True)

    user = relationship("User", back_populates="settings")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
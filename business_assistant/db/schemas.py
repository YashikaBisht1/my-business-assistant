"""Database schemas for Business Assistant.

Defines SQLAlchemy models for storing decisions, feedback, policies, and audit logs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, JSON,
    ForeignKey, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

from business_assistant.core.config import settings

Base = declarative_base()


class Decision(Base):
    """Stores decision records with structured outputs."""
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    question = Column(Text, nullable=True)
    computed_insights = Column(Text, nullable=True)
    summary_of_findings = Column(Text, nullable=False)
    policy_alignment = Column(Text, nullable=False)
    recommended_actions = Column(Text, nullable=False)
    limitations_confidence = Column(Text, nullable=False)
    user_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata (renamed from metadata to avoid SQLAlchemy conflict)
    
    # Relationships
    feedbacks = relationship("Feedback", back_populates="decision", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="decision", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "question": self.question,
            "summary_of_findings": self.summary_of_findings,
            "policy_alignment": self.policy_alignment,
            "recommended_actions": self.recommended_actions,
            "limitations_confidence": self.limitations_confidence,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.extra_metadata,
        }


class Policy(Base):
    """Stores policy documents with versioning."""
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    version = Column(String(50), nullable=False, default="1.0")
    category = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_metadata = Column(JSON, nullable=True)  # Renamed from metadata
    
    # Index for faster lookups
    __table_args__ = (
        Index("idx_policy_name_version", "name", "version"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "version": self.version,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.extra_metadata,
        }


class Feedback(Base):
    """Stores user feedback on decisions."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("decisions.id"), nullable=False, index=True)
    user_id = Column(String(100), nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 scale
    comment = Column(Text, nullable=True)
    is_helpful = Column(Boolean, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    extra_metadata = Column(JSON, nullable=True)  # Renamed from metadata
    
    # Relationships
    decision = relationship("Decision", back_populates="feedbacks")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "decision_id": self.decision_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "comment": self.comment,
            "is_helpful": self.is_helpful,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.extra_metadata,
        }


class AuditLog(Base):
    """Stores audit logs for compliance and tracking."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("decisions.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    decision = relationship("Decision", back_populates="audit_logs")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "decision_id": self.decision_id,
            "action": self.action,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class CacheEntry(Base):
    """Stores cached LLM responses."""
    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    cache_value = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    hit_count = Column(Integer, default=0)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "cache_key": self.cache_key,
            "cache_value": self.cache_value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "hit_count": self.hit_count,
        }


class User(Base):
    """Stores user information (for authentication)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Hashed password
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    extra_metadata = Column(JSON, nullable=True)  # Renamed from metadata

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


# Database engine and session
def get_database_url() -> str:
    """Get database URL based on configuration."""
    if settings.DB_TYPE == "postgresql":
        if not all([settings.DB_HOST, settings.DB_NAME, settings.DB_USER]):
            raise ValueError("PostgreSQL requires DB_HOST, DB_NAME, and DB_USER")
        password = settings.DB_PASSWORD or ""
        port = settings.DB_PORT or 5432
        return f"postgresql://{settings.DB_USER}:{password}@{settings.DB_HOST}:{port}/{settings.DB_NAME}"
    else:
        return f"sqlite:///{settings.DB_PATH}"


engine = create_engine(
    get_database_url(),
    connect_args={"check_same_thread": False} if settings.DB_TYPE == "sqlite" else {},
    echo=settings.ENABLE_DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


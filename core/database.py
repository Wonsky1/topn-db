"""
Database configuration and models for OLX Database FastAPI service.
"""

from datetime import datetime, timezone

import pytz
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# Warsaw timezone
WARSAW_TZ = pytz.timezone("Europe/Warsaw")

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def now_warsaw() -> datetime:
    """Get current datetime in Warsaw timezone as naive datetime."""
    utc_now = datetime.now(timezone.utc)
    warsaw_now = utc_now.astimezone(WARSAW_TZ)
    return warsaw_now.replace(tzinfo=None)  # Remove timezone info for database storage


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


class MonitoringTask(Base):
    """Model for monitoring tasks."""

    __tablename__ = "monitoring_tasks"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    name = Column(String(64), nullable=False)
    url = Column(String, nullable=False)
    last_updated = Column(DateTime, nullable=False)
    last_got_item = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("chat_id", "name", name="uix_chat_id_name"),)

    @classmethod
    def has_url_for_chat(cls, db: Session, chat_id: str, url: str) -> bool:
        """Return True if a monitoring for this URL already exists for this chat."""
        return (
            db.query(cls).filter(cls.chat_id == chat_id, cls.url == url).first()
            is not None
        )


class ItemRecord(Base):
    """Model for item records."""

    __tablename__ = "item_records"

    id = Column(Integer, primary_key=True, index=True)
    item_url = Column(String, unique=True, index=True)
    source_url = Column(
        String, nullable=False, index=True
    )  # URL from which this item was extracted
    title = Column(String)
    price = Column(String)
    location = Column(String)
    created_at = Column(DateTime)
    created_at_pretty = Column(String)
    image_url = Column(String, nullable=True)
    description = Column(String)
    first_seen = Column(DateTime, default=now_warsaw)

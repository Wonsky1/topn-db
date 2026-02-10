"""
Database configuration and models for OLX Database FastAPI service.
"""

from datetime import datetime, timezone

import pytz
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

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
    """
    Initialize database tables.

    DEPRECATED: This function auto-creates tables/columns and conflicts with Alembic migrations.
    Use `alembic upgrade head` instead to apply migrations properly.
    """
    Base.metadata.create_all(bind=engine)


# Association table for many-to-many relationship between MonitoringTask and District
monitoring_task_districts = Table(
    "monitoring_task_districts",
    Base.metadata,
    Column(
        "monitoring_task_id",
        Integer,
        ForeignKey("monitoring_tasks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "district_id",
        Integer,
        ForeignKey("districts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class MonitoringTask(Base):
    """Model for monitoring tasks."""

    __tablename__ = "monitoring_tasks"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    name = Column(String(64), nullable=False)
    url = Column(String, nullable=False)
    last_updated = Column(DateTime, nullable=False)
    last_got_item = Column(DateTime, nullable=True)

    # GraphQL capture fields
    graphql_endpoint = Column(String(500), nullable=True)
    graphql_payload = Column(JSON, nullable=True)
    graphql_headers = Column(JSON, nullable=True)
    graphql_captured_at = Column(DateTime, nullable=True)

    city_id = Column(
        Integer, ForeignKey("cities.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    city = relationship("City", back_populates="monitoring_tasks")
    allowed_districts = relationship(
        "District",
        secondary=monitoring_task_districts,
        back_populates="monitoring_tasks",
    )

    __table_args__ = (UniqueConstraint("chat_id", "name", name="uix_chat_id_name"),)

    @classmethod
    def has_url_for_chat(cls, db: Session, chat_id: str, url: str) -> bool:
        """Return True if a monitoring for this URL already exists for this chat."""
        return (
            db.query(cls).filter(cls.chat_id == chat_id, cls.url == url).first()
            is not None
        )


class City(Base):
    """Model for cities."""

    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name_raw = Column(String(255), nullable=False)
    name_normalized = Column(String(255), nullable=False, unique=True)

    # Relationships
    districts = relationship("District", back_populates="city")
    monitoring_tasks = relationship("MonitoringTask", back_populates="city")
    items = relationship("ItemRecord", back_populates="city")


class District(Base):
    """Model for districts."""

    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(
        Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False
    )
    name_raw = Column(String(255), nullable=False)
    name_normalized = Column(String(255), nullable=False)

    # Relationships
    city = relationship("City", back_populates="districts")
    monitoring_tasks = relationship(
        "MonitoringTask",
        secondary=monitoring_task_districts,
        back_populates="allowed_districts",
    )
    items = relationship("ItemRecord", back_populates="district")

    __table_args__ = (
        UniqueConstraint("city_id", "name_normalized", name="uix_city_district"),
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
    source = Column(String, nullable=True)
    first_seen = Column(DateTime, default=now_warsaw)
    city_id = Column(
        Integer, ForeignKey("cities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    district_id = Column(
        Integer,
        ForeignKey("districts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    city = relationship("City", back_populates="items")
    district = relationship("District", back_populates="items")

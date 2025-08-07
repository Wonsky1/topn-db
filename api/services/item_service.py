"""
Service layer for item record operations.
"""

from datetime import timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from core.config import settings
from core.database import ItemRecord, MonitoringTask, now_warsaw
from schemas.items import ItemRecordCreate


class ItemService:
    """Service class for item record operations."""

    @staticmethod
    def create_item(db: Session, item_data: ItemRecordCreate) -> ItemRecord:
        """Create a new item record."""
        # Determine source based on item URL
        source = item_data.source
        if not source and item_data.item_url:
            url_to_check = item_data.item_url
            if "olx.pl" in url_to_check.lower():
                source = "OLX"
            elif "otodom.pl" in url_to_check.lower():
                source = "Otodom"

        new_item = ItemRecord(
            item_url=item_data.item_url,
            source_url=item_data.source_url,
            title=item_data.title,
            price=item_data.price,
            location=item_data.location,
            created_at=item_data.created_at,
            created_at_pretty=item_data.created_at_pretty,
            image_url=item_data.image_url,
            description=item_data.description,
            source=source,
            first_seen=now_warsaw(),
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item

    @staticmethod
    def get_item_by_url(db: Session, item_url: str) -> Optional[ItemRecord]:
        """Get an item by its URL."""
        return db.query(ItemRecord).filter(ItemRecord.item_url == item_url).first()

    @staticmethod
    def get_items_by_source_url(
        db: Session, source_url: str, limit: int = 100
    ) -> List[ItemRecord]:
        """Get items by source URL."""
        return (
            db.query(ItemRecord)
            .filter(ItemRecord.source_url == source_url)
            .order_by(ItemRecord.first_seen.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_items_by_source(
        db: Session, source: str, limit: int = 100
    ) -> List[ItemRecord]:
        """Get items by source (OLX or Otodom)."""
        return (
            db.query(ItemRecord)
            .filter(ItemRecord.source == source)
            .order_by(ItemRecord.first_seen.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all_items(db: Session, skip: int = 0, limit: int = 100) -> List[ItemRecord]:
        """Get all items with pagination."""
        return db.query(ItemRecord).offset(skip).limit(limit).all()

    @staticmethod
    def get_items_count(db: Session) -> int:
        """Get total count of items."""
        return db.query(ItemRecord).count()

    @staticmethod
    def get_items_to_send_for_task(
        db: Session, task: MonitoringTask
    ) -> List[ItemRecord]:
        """
        Get a list of ItemRecords that should be sent for a given MonitoringTask.
        If the task has a 'last_got_item' timestamp, return items seen after that time.
        Otherwise, return items seen in the last DEFAULT_LAST_MINUTES_GETTING minutes.
        Filter items to only include those matching the exact monitoring source URL.
        """
        items_query = db.query(ItemRecord)

        if task.last_got_item:
            items_to_send = (
                items_query.filter(
                    ItemRecord.first_seen > task.last_got_item,
                    ItemRecord.source_url == task.url,
                )
                .order_by(ItemRecord.first_seen.desc())
                .all()
            )
        else:
            if (
                settings.DEFAULT_SENDING_FREQUENCY_MINUTES
                > settings.DEFAULT_LAST_MINUTES_GETTING
            ):
                time_threshold = now_warsaw() - timedelta(
                    minutes=settings.DEFAULT_SENDING_FREQUENCY_MINUTES
                )
            else:
                time_threshold = now_warsaw() - timedelta(
                    minutes=settings.DEFAULT_LAST_MINUTES_GETTING
                )
            items_to_send = (
                items_query.filter(
                    ItemRecord.first_seen > time_threshold,
                    ItemRecord.source_url == task.url,
                )
                .order_by(ItemRecord.first_seen.desc())
                .all()
            )

        return items_to_send

    @staticmethod
    def get_items_to_send_for_task_by_id(db: Session, task_id: int) -> List[ItemRecord]:
        """Get items to send for a task by task ID."""
        task = db.query(MonitoringTask).filter(MonitoringTask.id == task_id).first()
        if not task:
            return []
        return ItemService.get_items_to_send_for_task(db, task)

    @staticmethod
    def delete_items_older_than_n_days(db: Session, n: int) -> List[ItemRecord]:
        """
        Delete all items older than n days from now_warsaw.
        Returns deleted items list.
        """
        cutoff_date = now_warsaw() - timedelta(days=n)
        items_to_delete = (
            db.query(ItemRecord).filter(ItemRecord.first_seen < cutoff_date).all()
        )

        for item in items_to_delete:
            db.delete(item)

        db.commit()
        return items_to_delete

    @staticmethod
    def delete_item_by_id(db: Session, item_id: int) -> bool:
        """Delete an item by ID."""
        item = db.query(ItemRecord).filter(ItemRecord.id == item_id).first()
        if item:
            db.delete(item)
            db.commit()
            return True
        return False

    @staticmethod
    def get_recent_items(
        db: Session, hours: int = 24, limit: int = 100
    ) -> List[ItemRecord]:
        """Get items from the last N hours."""
        time_threshold = now_warsaw() - timedelta(hours=hours)
        return (
            db.query(ItemRecord)
            .filter(ItemRecord.first_seen > time_threshold)
            .order_by(ItemRecord.first_seen.desc())
            .limit(limit)
            .all()
        )

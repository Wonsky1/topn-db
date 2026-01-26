"""
Service layer for item record operations.
"""

from datetime import timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from unidecode import unidecode

from core.config import settings
from core.database import City, District, ItemRecord, MonitoringTask, now_warsaw
from schemas.items import ItemRecordCreate


class ItemService:
    """Service class for item record operations."""

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize a name using unidecode and lowercase."""
        return unidecode(name).lower().strip()

    @staticmethod
    def _parse_location(location: str) -> Tuple[str, str]:
        """
        Parse location string in format "City, District" or "City".
        Returns tuple of (city_name, district_name).
        If parsing fails or location is None/empty, returns ("Unknown", "Unknown").
        Note: Location should already be cleaned (no "Odświeżono" suffix) before calling this.
        """
        if not location or not location.strip():
            return ("Unknown", "Unknown")

        try:
            parts = [part.strip() for part in location.split(",")]
            if len(parts) >= 2:
                # Format: "Warszawa, Ursus"
                city_name = parts[0]
                district_name = parts[1]
            elif len(parts) == 1:
                # Format: "Warszawa" (no district)
                city_name = parts[0]
                district_name = "Unknown"
            else:
                return ("Unknown", "Unknown")

            return (city_name, district_name)
        except Exception:
            return ("Unknown", "Unknown")

    @staticmethod
    def _get_or_create_city(db: Session, city_name: str) -> City:
        """Get existing city or create new one."""
        city_normalized = ItemService._normalize_name(city_name)

        # Try to find existing city
        city = db.query(City).filter(City.name_normalized == city_normalized).first()

        if not city:
            # Create new city
            city = City(name_raw=city_name, name_normalized=city_normalized)
            db.add(city)
            db.flush()  # Flush to get the ID without committing

        return city

    @staticmethod
    def _get_or_create_district(
        db: Session, city: City, district_name: str
    ) -> District:
        """Get existing district or create new one for the given city."""
        district_normalized = ItemService._normalize_name(district_name)

        # Try to find existing district in this city
        district = (
            db.query(District)
            .filter(
                District.city_id == city.id,
                District.name_normalized == district_normalized,
            )
            .first()
        )

        if not district:
            # Create new district
            district = District(
                city_id=city.id,
                name_raw=district_name,
                name_normalized=district_normalized,
            )
            db.add(district)
            db.flush()  # Flush to get the ID without committing

        return district

    @staticmethod
    def create_item(db: Session, item_data: ItemRecordCreate) -> ItemRecord:
        """Create a new item record with automatic city/district parsing."""
        # Determine source based on item URL
        source = item_data.source
        if not source and item_data.item_url:
            url_to_check = item_data.item_url
            if "olx.pl" in url_to_check.lower():
                source = "OLX"
            elif "otodom.pl" in url_to_check.lower():
                source = "Otodom"

        # Clean location string by removing "Odświeżono" suffix
        clean_location = item_data.location
        if clean_location:
            clean_location = (
                clean_location.replace(" - Odświeżono", "")
                .replace(" - odświeżono", "")
                .strip()
            )

        # Parse location to get city and district
        city_name, district_name = ItemService._parse_location(clean_location)

        # Get or create city
        city = ItemService._get_or_create_city(db, city_name)

        # Get or create district
        district = ItemService._get_or_create_district(db, city, district_name)

        new_item = ItemRecord(
            item_url=item_data.item_url,
            source_url=item_data.source_url,
            title=item_data.title,
            price=item_data.price,
            location=clean_location,  # Store cleaned location
            created_at=item_data.created_at,
            created_at_pretty=item_data.created_at_pretty,
            image_url=item_data.image_url,
            description=item_data.description,
            source=source,
            first_seen=now_warsaw(),
            city_id=city.id,
            district_id=district.id,
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

        Location filtering:
        - If task has city_id: only include items from that city OR "Unknown" city
        - If task has allowed_districts: only include items from those districts OR "Unknown" district
        - Items with "Unknown" location are always included to avoid missing potentially relevant items
        """
        items_query = db.query(ItemRecord)

        # Determine time threshold
        if task.last_got_item:
            time_filter = ItemRecord.first_seen > task.last_got_item
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
            time_filter = ItemRecord.first_seen > time_threshold

        # Base filters: time and source URL
        items_query = items_query.filter(
            time_filter,
            ItemRecord.source_url == task.url,
        )

        # Apply city filtering if task has city_id
        if task.city_id:
            # Get "Unknown" city
            unknown_city = (
                db.query(City).filter(City.name_normalized == "unknown").first()
            )
            unknown_city_id = unknown_city.id if unknown_city else None

            # Include items from the specified city OR "Unknown" city
            if unknown_city_id:
                items_query = items_query.filter(
                    (ItemRecord.city_id == task.city_id)
                    | (ItemRecord.city_id == unknown_city_id)
                )
            else:
                items_query = items_query.filter(ItemRecord.city_id == task.city_id)

        # Apply district filtering if task has allowed_districts
        if task.allowed_districts:
            allowed_district_ids = [d.id for d in task.allowed_districts]

            # Get "Unknown" district
            unknown_district = (
                db.query(District).filter(District.name_normalized == "unknown").first()
            )
            unknown_district_id = unknown_district.id if unknown_district else None

            # Include items from allowed districts OR "Unknown" district
            if unknown_district_id:
                items_query = items_query.filter(
                    (ItemRecord.district_id.in_(allowed_district_ids))
                    | (ItemRecord.district_id == unknown_district_id)
                )
            else:
                items_query = items_query.filter(
                    ItemRecord.district_id.in_(allowed_district_ids)
                )

        items_to_send = items_query.order_by(ItemRecord.first_seen.desc()).all()
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

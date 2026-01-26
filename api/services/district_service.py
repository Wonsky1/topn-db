"""
Service layer for district operations.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from core.database import District
from schemas.districts import DistrictCreate, DistrictUpdate


class DistrictService:
    """Service class for district operations."""

    @staticmethod
    def get_all_districts(db: Session) -> List[District]:
        """Get all districts."""
        return db.query(District).order_by(District.name_normalized).all()

    @staticmethod
    def get_district_by_id(db: Session, district_id: int) -> Optional[District]:
        """Get a district by ID."""
        return db.query(District).filter(District.id == district_id).first()

    @staticmethod
    def get_districts_by_city_id(db: Session, city_id: int) -> List[District]:
        """Get all districts for a specific city."""
        return (
            db.query(District)
            .filter(District.city_id == city_id)
            .order_by(District.name_normalized)
            .all()
        )

    @staticmethod
    def create_district(db: Session, district_data: DistrictCreate) -> District:
        """Create a new district."""
        # Check if district with this normalized name already exists in this city
        existing_district = (
            db.query(District)
            .filter(
                District.city_id == district_data.city_id,
                District.name_normalized == district_data.name_normalized,
            )
            .first()
        )
        if existing_district:
            raise ValueError(
                f"District with normalized name '{district_data.name_normalized}' "
                f"already exists in city {district_data.city_id}"
            )

        new_district = District(
            city_id=district_data.city_id,
            name_raw=district_data.name_raw,
            name_normalized=district_data.name_normalized,
        )
        db.add(new_district)
        db.commit()
        db.refresh(new_district)
        return new_district

    @staticmethod
    def update_district(
        db: Session, district_id: int, district_data: DistrictUpdate
    ) -> Optional[District]:
        """Update a district."""
        district = DistrictService.get_district_by_id(db, district_id)
        if not district:
            return None

        if district_data.city_id is not None:
            district.city_id = district_data.city_id
        if district_data.name_raw is not None:
            district.name_raw = district_data.name_raw
        if district_data.name_normalized is not None:
            # Check if new normalized name conflicts with another district in the same city
            city_id = (
                district_data.city_id
                if district_data.city_id is not None
                else district.city_id
            )
            existing_district = (
                db.query(District)
                .filter(
                    District.city_id == city_id,
                    District.name_normalized == district_data.name_normalized,
                )
                .first()
            )
            if existing_district and existing_district.id != district_id:
                raise ValueError(
                    f"District with normalized name '{district_data.name_normalized}' "
                    f"already exists in city {city_id}"
                )
            district.name_normalized = district_data.name_normalized

        db.commit()
        db.refresh(district)
        return district

    @staticmethod
    def delete_district_by_id(db: Session, district_id: int) -> bool:
        """Delete a district by ID."""
        district = DistrictService.get_district_by_id(db, district_id)
        if district:
            db.delete(district)
            db.commit()
            return True
        return False

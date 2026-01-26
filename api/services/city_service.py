"""
Service layer for city operations.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from core.database import City
from schemas.cities import CityCreate, CityUpdate


class CityService:
    """Service class for city operations."""

    @staticmethod
    def get_all_cities(db: Session) -> List[City]:
        """Get all cities."""
        return db.query(City).order_by(City.name_normalized).all()

    @staticmethod
    def get_city_by_id(db: Session, city_id: int) -> Optional[City]:
        """Get a city by ID."""
        return db.query(City).filter(City.id == city_id).first()

    @staticmethod
    def get_city_by_normalized_name(
        db: Session, name_normalized: str
    ) -> Optional[City]:
        """Get a city by normalized name."""
        return db.query(City).filter(City.name_normalized == name_normalized).first()

    @staticmethod
    def create_city(db: Session, city_data: CityCreate) -> City:
        """Create a new city."""
        # Check if city with this normalized name already exists
        existing_city = CityService.get_city_by_normalized_name(
            db, city_data.name_normalized
        )
        if existing_city:
            raise ValueError(
                f"City with normalized name '{city_data.name_normalized}' already exists"
            )

        new_city = City(
            name_raw=city_data.name_raw,
            name_normalized=city_data.name_normalized,
        )
        db.add(new_city)
        db.commit()
        db.refresh(new_city)
        return new_city

    @staticmethod
    def update_city(db: Session, city_id: int, city_data: CityUpdate) -> Optional[City]:
        """Update a city."""
        city = CityService.get_city_by_id(db, city_id)
        if not city:
            return None

        if city_data.name_raw is not None:
            city.name_raw = city_data.name_raw
        if city_data.name_normalized is not None:
            # Check if new normalized name conflicts with another city
            existing_city = CityService.get_city_by_normalized_name(
                db, city_data.name_normalized
            )
            if existing_city and existing_city.id != city_id:
                raise ValueError(
                    f"City with normalized name '{city_data.name_normalized}' already exists"
                )
            city.name_normalized = city_data.name_normalized

        db.commit()
        db.refresh(city)
        return city

    @staticmethod
    def delete_city_by_id(db: Session, city_id: int) -> bool:
        """Delete a city by ID."""
        city = CityService.get_city_by_id(db, city_id)
        if city:
            db.delete(city)
            db.commit()
            return True
        return False

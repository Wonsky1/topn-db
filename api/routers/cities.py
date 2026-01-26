"""
API router for city operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.services.city_service import CityService
from api.services.district_service import DistrictService
from core.database import get_db
from schemas.cities import (
    CityCreate,
    CityList,
    CityResponse,
    CityUpdate,
    CityWithDistrictsResponse,
)
from schemas.districts import DistrictList

router = APIRouter(prefix="/cities", tags=["Cities"])


@router.get(
    "/",
    response_model=CityList,
    summary="Get all cities",
    description="Retrieve all cities from the database",
)
async def get_all_cities(db: Session = Depends(get_db)):
    """Get all cities."""
    cities = CityService.get_all_cities(db)
    return CityList(cities=cities, total=len(cities))


@router.get(
    "/by-name/{name_normalized}",
    response_model=CityResponse,
    summary="Get city by normalized name",
    description="Retrieve a specific city by its normalized name",
)
async def get_city_by_normalized_name(
    name_normalized: str, db: Session = Depends(get_db)
):
    """Get a city by normalized name."""
    city = CityService.get_city_by_normalized_name(db, name_normalized)
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with normalized name '{name_normalized}' not found",
        )
    return city


@router.get(
    "/{city_id}",
    response_model=CityResponse,
    summary="Get city by ID",
    description="Retrieve a specific city by its ID",
)
async def get_city_by_id(city_id: int, db: Session = Depends(get_db)):
    """Get a city by ID."""
    city = CityService.get_city_by_id(db, city_id)
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with ID {city_id} not found",
        )
    return city


@router.get(
    "/{city_id}/with-districts",
    response_model=CityWithDistrictsResponse,
    summary="Get city with districts",
    description="Retrieve a city with all its districts",
)
async def get_city_with_districts(city_id: int, db: Session = Depends(get_db)):
    """Get a city with all its districts."""
    city = CityService.get_city_by_id(db, city_id)
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with ID {city_id} not found",
        )
    return city


@router.get(
    "/{city_id}/districts",
    response_model=DistrictList,
    summary="Get districts for city",
    description="Retrieve all districts for a specific city",
)
async def get_districts_for_city(city_id: int, db: Session = Depends(get_db)):
    """Get all districts for a city."""
    city = CityService.get_city_by_id(db, city_id)
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with ID {city_id} not found",
        )
    districts = DistrictService.get_districts_by_city_id(db, city_id)
    return DistrictList(districts=districts, total=len(districts))


@router.post(
    "/",
    response_model=CityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create city",
    description="Create a new city",
)
async def create_city(city_data: CityCreate, db: Session = Depends(get_db)):
    """Create a new city."""
    try:
        city = CityService.create_city(db, city_data)
        return city
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{city_id}",
    response_model=CityResponse,
    summary="Update city",
    description="Update an existing city",
)
async def update_city(
    city_id: int, city_data: CityUpdate, db: Session = Depends(get_db)
):
    """Update a city."""
    try:
        city = CityService.update_city(db, city_id, city_data)
        if not city:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City with ID {city_id} not found",
            )
        return city
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{city_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete city",
    description="Delete a city by ID",
)
async def delete_city_by_id(city_id: int, db: Session = Depends(get_db)):
    """Delete a city by ID."""
    success = CityService.delete_city_by_id(db, city_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with ID {city_id} not found",
        )

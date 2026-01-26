"""
API router for district operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.services.district_service import DistrictService
from core.database import get_db
from schemas.districts import (
    DistrictCreate,
    DistrictList,
    DistrictResponse,
    DistrictUpdate,
    DistrictWithCityResponse,
)

router = APIRouter(prefix="/districts", tags=["Districts"])


@router.get(
    "/",
    response_model=DistrictList,
    summary="Get all districts",
    description="Retrieve all districts from the database",
)
async def get_all_districts(db: Session = Depends(get_db)):
    """Get all districts."""
    districts = DistrictService.get_all_districts(db)
    return DistrictList(districts=districts, total=len(districts))


@router.get(
    "/{district_id}",
    response_model=DistrictResponse,
    summary="Get district by ID",
    description="Retrieve a specific district by its ID",
)
async def get_district_by_id(district_id: int, db: Session = Depends(get_db)):
    """Get a district by ID."""
    district = DistrictService.get_district_by_id(db, district_id)
    if not district:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District with ID {district_id} not found",
        )
    return district


@router.get(
    "/{district_id}/with-city",
    response_model=DistrictWithCityResponse,
    summary="Get district with city",
    description="Retrieve a district with its parent city information",
)
async def get_district_with_city(district_id: int, db: Session = Depends(get_db)):
    """Get a district with its city."""
    district = DistrictService.get_district_by_id(db, district_id)
    if not district:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District with ID {district_id} not found",
        )
    return district


@router.get(
    "/city/{city_id}",
    response_model=DistrictList,
    summary="Get districts by city ID",
    description="Retrieve all districts for a specific city",
)
async def get_districts_by_city_id(city_id: int, db: Session = Depends(get_db)):
    """Get all districts for a city."""
    districts = DistrictService.get_districts_by_city_id(db, city_id)
    return DistrictList(districts=districts, total=len(districts))


@router.post(
    "/",
    response_model=DistrictResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create district",
    description="Create a new district",
)
async def create_district(district_data: DistrictCreate, db: Session = Depends(get_db)):
    """Create a new district."""
    try:
        district = DistrictService.create_district(db, district_data)
        return district
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{district_id}",
    response_model=DistrictResponse,
    summary="Update district",
    description="Update an existing district",
)
async def update_district(
    district_id: int, district_data: DistrictUpdate, db: Session = Depends(get_db)
):
    """Update a district."""
    try:
        district = DistrictService.update_district(db, district_id, district_data)
        if not district:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"District with ID {district_id} not found",
            )
        return district
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{district_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete district",
    description="Delete a district by ID",
)
async def delete_district_by_id(district_id: int, db: Session = Depends(get_db)):
    """Delete a district by ID."""
    success = DistrictService.delete_district_by_id(db, district_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District with ID {district_id} not found",
        )

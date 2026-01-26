"""
Pydantic schemas for districts.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DistrictBase(BaseModel):
    """Base schema for districts."""

    city_id: int = Field(..., description="ID of the city this district belongs to")
    name_raw: str = Field(..., max_length=255, description="Raw district name")
    name_normalized: str = Field(
        ..., max_length=255, description="Normalized district name"
    )


class DistrictCreate(DistrictBase):
    """Schema for creating a district."""


class DistrictUpdate(BaseModel):
    """Schema for updating a district."""

    city_id: Optional[int] = Field(
        None, description="ID of the city this district belongs to"
    )
    name_raw: Optional[str] = Field(
        None, max_length=255, description="Raw district name"
    )
    name_normalized: Optional[str] = Field(
        None, max_length=255, description="Normalized district name"
    )


class DistrictResponse(DistrictBase):
    """Schema for district response."""

    id: int

    model_config = ConfigDict(from_attributes=True)


class DistrictWithCityResponse(DistrictResponse):
    """Schema for district response with city."""

    city: CityResponse

    model_config = ConfigDict(from_attributes=True)


class DistrictList(BaseModel):
    """Schema for list of districts."""

    districts: list[DistrictResponse]
    total: int


# Import to resolve forward references
from .cities import CityResponse  # noqa: E402

# Rebuild models to resolve forward references
DistrictWithCityResponse.model_rebuild()

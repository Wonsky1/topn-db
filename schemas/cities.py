"""
Pydantic schemas for cities.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CityBase(BaseModel):
    """Base schema for cities."""

    name_raw: str = Field(..., max_length=255, description="Raw city name")
    name_normalized: str = Field(
        ..., max_length=255, description="Normalized city name (unique)"
    )


class CityCreate(CityBase):
    """Schema for creating a city."""


class CityUpdate(BaseModel):
    """Schema for updating a city."""

    name_raw: Optional[str] = Field(None, max_length=255, description="Raw city name")
    name_normalized: Optional[str] = Field(
        None, max_length=255, description="Normalized city name (unique)"
    )


class CityResponse(CityBase):
    """Schema for city response."""

    id: int

    model_config = ConfigDict(from_attributes=True)


class CityWithDistrictsResponse(CityResponse):
    """Schema for city response with districts."""

    districts: list[DistrictResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CityList(BaseModel):
    """Schema for list of cities."""

    cities: list[CityResponse]
    total: int


# Import to resolve forward references
from .districts import DistrictResponse  # noqa: E402

# Rebuild models to resolve forward references
CityWithDistrictsResponse.model_rebuild()

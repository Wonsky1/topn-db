"""
Pydantic schemas for monitoring tasks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MonitoringTaskBase(BaseModel):
    """Base schema for monitoring tasks."""

    chat_id: str = Field(..., description="Chat ID for the monitoring task")
    name: str = Field(..., max_length=64, description="Name of the monitoring task")
    url: str = Field(..., description="URL to monitor")
    city_id: Optional[int] = Field(
        None, description="City ID to filter items by location"
    )


class MonitoringTaskCreate(MonitoringTaskBase):
    """Schema for creating a monitoring task."""

    allowed_district_ids: list[int] = Field(
        default_factory=list,
        description="List of district IDs to allow (empty means all districts in city)",
    )


class MonitoringTaskUpdate(BaseModel):
    """Schema for updating a monitoring task."""

    name: Optional[str] = Field(
        None, max_length=64, description="Name of the monitoring task"
    )
    url: Optional[str] = Field(None, description="URL to monitor")
    city_id: Optional[int] = Field(
        None, description="City ID to filter items by location"
    )
    allowed_district_ids: Optional[list[int]] = Field(
        None,
        description="List of district IDs to allow (empty means all districts in city)",
    )


class MonitoringTaskResponse(MonitoringTaskBase):
    """Schema for monitoring task response."""

    id: int
    last_updated: datetime
    last_got_item: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MonitoringTaskWithRelationsResponse(MonitoringTaskResponse):
    """Schema for monitoring task response with related city and districts."""

    city: Optional[CityResponse] = None
    allowed_districts: list[DistrictResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MonitoringTaskList(BaseModel):
    """Schema for list of monitoring tasks."""

    tasks: list[MonitoringTaskResponse]
    total: int


# Import to resolve forward references
from .cities import CityResponse  # noqa: E402
from .districts import DistrictResponse  # noqa: E402

# Rebuild models to resolve forward references
MonitoringTaskWithRelationsResponse.model_rebuild()

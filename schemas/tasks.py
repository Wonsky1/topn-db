"""
Pydantic schemas for monitoring tasks.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MonitoringTaskBase(BaseModel):
    """Base schema for monitoring tasks."""

    chat_id: str = Field(..., description="Chat ID for the monitoring task")
    name: str = Field(..., max_length=64, description="Name of the monitoring task")
    url: str = Field(..., description="URL to monitor")


class MonitoringTaskCreate(MonitoringTaskBase):
    """Schema for creating a monitoring task."""


class MonitoringTaskUpdate(BaseModel):
    """Schema for updating a monitoring task."""

    name: Optional[str] = Field(
        None, max_length=64, description="Name of the monitoring task"
    )
    url: Optional[str] = Field(None, description="URL to monitor")


class MonitoringTaskResponse(MonitoringTaskBase):
    """Schema for monitoring task response."""

    id: int
    last_updated: datetime
    last_got_item: Optional[datetime] = None

    class Config:
        from_attributes = True


class MonitoringTaskList(BaseModel):
    """Schema for list of monitoring tasks."""

    tasks: list[MonitoringTaskResponse]
    total: int

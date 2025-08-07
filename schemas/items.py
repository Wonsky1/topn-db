"""
Pydantic schemas for item records.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ItemRecordBase(BaseModel):
    """Base schema for item records."""

    item_url: str = Field(..., description="URL of the item")
    source_url: str = Field(
        ..., description="Source URL from which this item was extracted"
    )
    title: Optional[str] = Field(None, description="Title of the item")
    price: Optional[str] = Field(None, description="Price of the item")
    location: Optional[str] = Field(None, description="Location of the item")
    created_at: Optional[datetime] = Field(
        None, description="Creation date from the source"
    )
    created_at_pretty: Optional[str] = Field(
        None, description="Pretty formatted creation date"
    )
    image_url: Optional[str] = Field(None, description="Image URL of the item")
    description: Optional[str] = Field(None, description="Description of the item")
    source: Optional[str] = Field(
        None, description="Source of the item (OLX or Otodom)"
    )


class ItemRecordCreate(ItemRecordBase):
    """Schema for creating an item record."""


class ItemRecordResponse(ItemRecordBase):
    """Schema for item record response."""

    id: int
    first_seen: datetime

    class Config:
        from_attributes = True


class ItemRecordList(BaseModel):
    """Schema for list of item records."""

    items: list[ItemRecordResponse]
    total: int


class ItemsToSendResponse(BaseModel):
    """Schema for items to send for a task."""

    task_id: int
    task_name: str
    chat_id: str
    items: list[ItemRecordResponse]
    count: int

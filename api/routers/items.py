"""
API router for item record operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from api.services.item_service import ItemService
from core.database import ItemRecord, get_db
from schemas.items import ItemRecordCreate, ItemRecordList, ItemRecordResponse

router = APIRouter(prefix="/items", tags=["Item Records"])


@router.get(
    "/",
    response_model=ItemRecordList,
    summary="Get all items",
    description="Retrieve all item records with pagination",
)
async def get_all_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of items to return"
    ),
    db: Session = Depends(get_db),
):
    """Get all item records with pagination."""
    items = ItemService.get_all_items(db, skip=skip, limit=limit)
    total = ItemService.get_items_count(db)
    return ItemRecordList(items=items, total=total)


@router.get(
    "/by-source",
    response_model=ItemRecordList,
    summary="Get items by source URL",
    description="Retrieve items filtered by source URL",
)
async def get_items_by_source_url(
    source_url: str = Query(..., description="Source URL to filter by"),
    limit: int = Query(
        100, ge=1, le=10000, description="Maximum number of items to return"
    ),
    db: Session = Depends(get_db),
):
    """Get items by source URL."""
    items = ItemService.get_items_by_source_url(db, source_url, limit=limit)
    return ItemRecordList(items=items, total=len(items))


@router.get(
    "/recent",
    response_model=ItemRecordList,
    summary="Get recent items",
    description="Retrieve items from the last N hours",
)
async def get_recent_items(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of items to return"
    ),
    db: Session = Depends(get_db),
):
    """Get recent items from the last N hours."""
    items = ItemService.get_recent_items(db, hours=hours, limit=limit)
    return ItemRecordList(items=items, total=len(items))


@router.get(
    "/{item_id}",
    response_model=ItemRecordResponse,
    summary="Get item by ID",
    description="Retrieve a specific item record by its ID",
)
async def get_item_by_id(item_id: int, db: Session = Depends(get_db)):
    """Get an item record by ID."""
    item = db.query(ItemRecord).filter(ItemRecord.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )
    return item


@router.get(
    "/by-url/{item_url:path}",
    response_model=ItemRecordResponse,
    summary="Get item by URL",
    description="Retrieve a specific item record by its URL",
)
async def get_item_by_url(item_url: str, db: Session = Depends(get_db)):
    """Get an item record by URL."""
    item = ItemService.get_item_by_url(db, item_url)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with URL {item_url} not found",
        )
    return item


@router.post(
    "/",
    response_model=ItemRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create item record",
    description="Create a new item record",
)
async def create_item(item_data: ItemRecordCreate, db: Session = Depends(get_db)):
    """Create a new item record."""
    # Check if item with this URL already exists
    existing_item = ItemService.get_item_by_url(db, item_data.item_url)
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item with URL {item_data.item_url} already exists",
        )

    item = ItemService.create_item(db, item_data)
    return item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete item record",
    description="Delete an item record by ID",
)
async def delete_item_by_id(item_id: int, db: Session = Depends(get_db)):
    """Delete an item record by ID."""
    success = ItemService.delete_item_by_id(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )


@router.delete(
    "/cleanup/older-than/{days}",
    summary="Delete old items",
    description="Delete all items older than N days",
)
async def delete_items_older_than_n_days(
    days: int = Path(..., ge=1, description="Number of days to keep items for."),
    db: Session = Depends(get_db),
):
    """Delete items older than N days."""
    deleted_items = ItemService.delete_items_older_than_n_days(db, days)
    return {
        "message": f"Deleted {len(deleted_items)} items older than {days} days",
        "deleted_count": len(deleted_items),
        "deleted_items": [
            {"id": item.id, "item_url": item.item_url} for item in deleted_items
        ],
    }

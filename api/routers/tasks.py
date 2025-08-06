"""
API router for monitoring task operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.services.item_service import ItemService
from api.services.task_service import TaskService
from core.database import get_db
from schemas.items import ItemsToSendResponse
from schemas.tasks import (
    MonitoringTaskCreate,
    MonitoringTaskList,
    MonitoringTaskResponse,
    MonitoringTaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["Monitoring Tasks"])


@router.get(
    "/",
    response_model=MonitoringTaskList,
    summary="Get all monitoring tasks",
    description="Retrieve all monitoring tasks from the database",
)
async def get_all_tasks(db: Session = Depends(get_db)):
    """Get all monitoring tasks."""
    tasks = TaskService.get_all_tasks(db)
    return MonitoringTaskList(tasks=tasks, total=len(tasks))


@router.get(
    "/chat/{chat_id}",
    response_model=MonitoringTaskList,
    summary="Get tasks by chat ID",
    description="Retrieve all monitoring tasks for a specific chat ID",
)
async def get_tasks_by_chat_id(chat_id: str, db: Session = Depends(get_db)):
    """Get monitoring tasks by chat ID."""
    tasks = TaskService.get_tasks_by_chat_id(db, chat_id)
    return MonitoringTaskList(tasks=tasks, total=len(tasks))


@router.get(
    "/{task_id}",
    response_model=MonitoringTaskResponse,
    summary="Get task by ID",
    description="Retrieve a specific monitoring task by its ID",
)
async def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    """Get a monitoring task by ID."""
    task = TaskService.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return task


@router.post(
    "/",
    response_model=MonitoringTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create monitoring task",
    description="Create a new monitoring task",
)
async def create_task(task_data: MonitoringTaskCreate, db: Session = Depends(get_db)):
    """Create a new monitoring task."""
    try:
        task = TaskService.create_task(db, task_data)
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{task_id}",
    response_model=MonitoringTaskResponse,
    summary="Update monitoring task",
    description="Update an existing monitoring task",
)
async def update_task(
    task_id: int, task_data: MonitoringTaskUpdate, db: Session = Depends(get_db)
):
    """Update a monitoring task."""
    task = TaskService.update_task(db, task_id, task_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete monitoring task",
    description="Delete a monitoring task by ID",
)
async def delete_task_by_id(task_id: int, db: Session = Depends(get_db)):
    """Delete a monitoring task by ID."""
    success = TaskService.delete_task_by_id(db, task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )


@router.delete(
    "/chat/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tasks by chat ID",
    description="Delete all monitoring tasks for a specific chat ID, or a specific task by name",
)
async def delete_tasks_by_chat_id(
    chat_id: str, name: str = None, db: Session = Depends(get_db)
):
    """Delete monitoring tasks by chat ID, optionally filtered by name."""
    success = TaskService.delete_task_by_chat_id(db, chat_id, name)
    if not success:
        if name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with name '{name}' not found for chat {chat_id}",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No tasks found for chat {chat_id}",
            )


@router.get(
    "/pending",
    response_model=MonitoringTaskList,
    summary="Get pending tasks",
    description="Get tasks that are ready for processing based on frequency settings",
)
async def get_pending_tasks(db: Session = Depends(get_db)):
    """Get pending monitoring tasks."""
    tasks = TaskService.get_pending_tasks(db)
    return MonitoringTaskList(tasks=tasks, total=len(tasks))


@router.post(
    "/{task_id}/update-last-got-item",
    status_code=status.HTTP_200_OK,
    summary="Update last got item timestamp",
    description="Update the last_got_item timestamp for a task",
)
async def update_last_got_item(task_id: int, db: Session = Depends(get_db)):
    """Update the last_got_item timestamp for a task."""
    success = TaskService.update_last_got_item_by_id(db, task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return {"message": "Last got item timestamp updated successfully"}


@router.get(
    "/{task_id}/items-to-send",
    response_model=ItemsToSendResponse,
    summary="Get items to send for task",
    description="Get items that should be sent for a specific monitoring task",
)
async def get_items_to_send_for_task(task_id: int, db: Session = Depends(get_db)):
    """Get items to send for a specific task."""
    task = TaskService.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    items = ItemService.get_items_to_send_for_task(db, task)
    return ItemsToSendResponse(
        task_id=task.id,
        task_name=task.name,
        chat_id=task.chat_id,
        items=items,
        count=len(items),
    )

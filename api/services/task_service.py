"""
Service layer for monitoring task operations.
"""

from datetime import timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from core.config import settings
from core.database import MonitoringTask, now_warsaw
from schemas.tasks import MonitoringTaskCreate, MonitoringTaskUpdate


class TaskService:
    """Service class for monitoring task operations."""

    @staticmethod
    def get_tasks_by_chat_id(db: Session, chat_id: str) -> List[MonitoringTask]:
        """Fetch all monitoring tasks for chat ID."""
        return db.query(MonitoringTask).filter(MonitoringTask.chat_id == chat_id).all()

    @staticmethod
    def get_task_by_chat_and_name(
        db: Session, chat_id: str, name: str
    ) -> Optional[MonitoringTask]:
        """Fetch a monitoring task by chat ID and name."""
        return (
            db.query(MonitoringTask)
            .filter(MonitoringTask.chat_id == chat_id, MonitoringTask.name == name)
            .first()
        )

    @staticmethod
    def get_task_by_id(db: Session, task_id: int) -> Optional[MonitoringTask]:
        """Fetch a monitoring task by ID."""
        return db.query(MonitoringTask).filter(MonitoringTask.id == task_id).first()

    @staticmethod
    def get_all_tasks(db: Session) -> List[MonitoringTask]:
        """Get all monitoring tasks from the database."""
        return db.query(MonitoringTask).all()

    @staticmethod
    def create_task(db: Session, task_data: MonitoringTaskCreate) -> MonitoringTask:
        """Create a new monitoring task."""
        # Check if URL already exists for this chat
        if MonitoringTask.has_url_for_chat(db, task_data.chat_id, task_data.url):
            raise ValueError(
                f"URL {task_data.url} is already being monitored for chat {task_data.chat_id}"
            )

        new_task = MonitoringTask(
            chat_id=task_data.chat_id,
            name=task_data.name,
            url=task_data.url,
            last_updated=now_warsaw(),
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task

    @staticmethod
    def update_task(
        db: Session, task_id: int, task_data: MonitoringTaskUpdate
    ) -> Optional[MonitoringTask]:
        """Update a monitoring task."""
        task = TaskService.get_task_by_id(db, task_id)
        if not task:
            return None

        if task_data.name is not None:
            task.name = task_data.name
        if task_data.url is not None:
            task.url = task_data.url

        task.last_updated = now_warsaw()
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task_by_chat_id(
        db: Session, chat_id: str, name: Optional[str] = None
    ) -> bool:
        """Delete monitoring task(s) for given chat; if name provided delete only that monitoring."""
        if name:
            task = TaskService.get_task_by_chat_and_name(db, chat_id, name)
            if task:
                db.delete(task)
                db.commit()
                return True
            return False
        else:
            # Delete all tasks for chat
            tasks = TaskService.get_tasks_by_chat_id(db, chat_id)
            if tasks:
                for task in tasks:
                    db.delete(task)
                db.commit()
                return True
            return False

    @staticmethod
    def delete_task_by_id(db: Session, task_id: int) -> bool:
        """Delete a monitoring task by ID."""
        task = TaskService.get_task_by_id(db, task_id)
        if task:
            db.delete(task)
            db.commit()
            return True
        return False

    @staticmethod
    def get_pending_tasks(db: Session) -> List[MonitoringTask]:
        """
        Retrieve tasks where the last_got_item is either None or older than DEFAULT_SENDING_FREQUENCY_MINUTES.
        """
        time_threshold = now_warsaw() - timedelta(
            minutes=settings.DEFAULT_SENDING_FREQUENCY_MINUTES
        )
        tasks = (
            db.query(MonitoringTask)
            .filter(
                (MonitoringTask.last_got_item == None)
                | (MonitoringTask.last_got_item < time_threshold)
            )
            .all()
        )
        return tasks

    @staticmethod
    def update_last_got_item(db: Session, chat_id: str) -> bool:
        """Update the last_got_item timestamp for a given chat ID."""
        task = (
            db.query(MonitoringTask).filter(MonitoringTask.chat_id == chat_id).first()
        )
        if task:
            task.last_got_item = now_warsaw()
            db.commit()
            return True
        return False

    @staticmethod
    def update_last_got_item_by_id(db: Session, task_id: int) -> bool:
        """Update the last_got_item timestamp for a given task ID."""
        task = TaskService.get_task_by_id(db, task_id)
        if task:
            task.last_got_item = now_warsaw()
            db.commit()
            return True
        return False

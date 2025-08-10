import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from api.services.task_service import TaskService
from core.database import MonitoringTask
from schemas.tasks import MonitoringTaskCreate, MonitoringTaskUpdate


class TestTaskService(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock(spec=Session)

    def test_create_task_conflict(self):
        task_data = MonitoringTaskCreate(chat_id="c1", name="n1", url="http://test.com")
        self.db.query.return_value.filter.return_value.first.return_value = (
            MonitoringTask()
        )  # Mock existing task

        with patch("core.database.MonitoringTask.has_url_for_chat", return_value=True):
            with self.assertRaises(ValueError):
                TaskService.create_task(self.db, task_data)

    def test_update_non_existent_task(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        task_data = MonitoringTaskUpdate(name="new_name")
        result = TaskService.update_task(self.db, 999, task_data)
        self.assertIsNone(result)

    def test_update_task_fields(self):
        mock_task = MonitoringTask(id=1, name="old_name", url="http://old.com")
        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        # Update only name
        update_data_name = MonitoringTaskUpdate(name="new_name")
        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task_name = TaskService.update_task(self.db, 1, update_data_name)
            self.assertEqual(updated_task_name.name, "new_name")
            self.assertEqual(updated_task_name.url, "http://old.com")

        # Update only url
        update_data_url = MonitoringTaskUpdate(url="http://new.com")
        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task_url = TaskService.update_task(self.db, 1, update_data_url)
            self.assertEqual(
                updated_task_url.name, "new_name"
            )  # Name from previous update
            self.assertEqual(updated_task_url.url, "http://new.com")

    def test_delete_non_existent_task_by_id(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = TaskService.delete_task_by_id(self.db, 999)
        self.assertFalse(result)

    def test_delete_non_existent_task_by_chat_id(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = TaskService.delete_task_by_chat_id(self.db, "c1", "non_existent_name")
        self.assertFalse(result)

    def test_delete_tasks_for_chat_with_no_tasks(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = TaskService.delete_task_by_chat_id(self.db, "c_no_tasks")
        self.assertFalse(result)

    def test_get_pending_tasks(self):
        now = datetime(2025, 1, 1, 12, 0, 0)
        old_time = now - timedelta(minutes=60)
        new_time = now - timedelta(minutes=5)

        task1 = MonitoringTask(id=1, last_got_item=None)  # Pending
        task2 = MonitoringTask(id=2, last_got_item=old_time)  # Pending
        task3 = MonitoringTask(id=3, last_got_item=new_time)  # Not pending

        self.db.query.return_value.filter.return_value.all.return_value = [task1, task2]

        with patch("api.services.task_service.now_warsaw", lambda: now):
            with patch(
                "api.services.task_service.settings.DEFAULT_SENDING_FREQUENCY_MINUTES",
                30,
            ):
                pending_tasks = TaskService.get_pending_tasks(self.db)
                self.assertEqual(len(pending_tasks), 2)
                self.assertIn(task1, pending_tasks)
                self.assertIn(task2, pending_tasks)

    def test_update_last_got_item_by_id_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = TaskService.update_last_got_item_by_id(self.db, 999)
        self.assertFalse(result)

    def test_update_last_got_item_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = TaskService.update_last_got_item(self.db, "non_existent_chat")
        self.assertFalse(result)

    def test_update_last_got_item_found(self):
        mock_task = MonitoringTask(id=1, chat_id="c1")
        self.db.query.return_value.filter.return_value.first.return_value = mock_task
        with patch("api.services.task_service.now_warsaw") as mock_now:
            result = TaskService.update_last_got_item(self.db, "c1")
            self.assertTrue(result)
            self.assertIsNotNone(mock_task.last_got_item)
            mock_now.assert_called_once()


if __name__ == "__main__":
    unittest.main()

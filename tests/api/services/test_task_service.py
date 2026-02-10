import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from api.services.task_service import TaskService
from core.database import District, MonitoringTask
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

    def test_create_task_without_districts(self):
        """Test creating a task without allowed districts."""
        task_data = MonitoringTaskCreate(
            chat_id="c1",
            name="n1",
            url="http://test.com",
            city_id=1,
            allowed_district_ids=[],
        )

        with patch(
            "core.database.MonitoringTask.has_url_for_chat", return_value=False
        ), patch("api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)):
            TaskService.create_task(self.db, task_data)

            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()

    def test_update_task_city_and_districts(self):
        """Test updating task city and allowed districts."""
        mock_task = MagicMock(spec=MonitoringTask)
        mock_task.id = 1
        mock_task.name = "old_name"
        mock_task.url = "http://old.com"
        mock_task.city_id = 1
        mock_task.allowed_districts = []

        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        district1 = MagicMock(spec=District)
        district1.id = 5
        district2 = MagicMock(spec=District)
        district2.id = 6
        self.db.query.return_value.filter.return_value.all.return_value = [
            district1,
            district2,
        ]

        update_data = MonitoringTaskUpdate(city_id=2, allowed_district_ids=[5, 6])

        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task = TaskService.update_task(self.db, 1, update_data)
            self.assertEqual(updated_task.city_id, 2)

    def test_update_task_clear_districts(self):
        """Test clearing allowed districts from a task."""
        mock_task = MagicMock(spec=MonitoringTask)
        mock_task.id = 1
        mock_task.name = "old_name"
        mock_task.url = "http://old.com"
        mock_task.allowed_districts = ["district1", "district2"]

        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        update_data = MonitoringTaskUpdate(allowed_district_ids=[])

        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task = TaskService.update_task(self.db, 1, update_data)
            self.assertEqual(updated_task.allowed_districts, [])

    def test_get_all_tasks(self):
        """Test getting all tasks."""
        mock_tasks = [
            MonitoringTask(id=1, name="task1"),
            MonitoringTask(id=2, name="task2"),
        ]
        self.db.query.return_value.all.return_value = mock_tasks

        result = TaskService.get_all_tasks(self.db)
        self.assertEqual(result, mock_tasks)

    def test_get_tasks_by_chat_id(self):
        """Test getting tasks by chat ID."""
        mock_tasks = [MonitoringTask(id=1, chat_id="c1")]
        self.db.query.return_value.filter.return_value.all.return_value = mock_tasks

        result = TaskService.get_tasks_by_chat_id(self.db, "c1")
        self.assertEqual(result, mock_tasks)

    def test_get_task_by_chat_and_name(self):
        """Test getting task by chat ID and name."""
        mock_task = MonitoringTask(id=1, chat_id="c1", name="task1")
        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        result = TaskService.get_task_by_chat_and_name(self.db, "c1", "task1")
        self.assertEqual(result, mock_task)

    def test_get_task_by_id(self):
        """Test getting task by ID."""
        mock_task = MonitoringTask(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        result = TaskService.get_task_by_id(self.db, 1)
        self.assertEqual(result, mock_task)

    def test_delete_task_by_chat_id_with_name(self):
        """Test deleting a specific task by chat ID and name."""
        mock_task = MonitoringTask(id=1, chat_id="c1", name="task1")
        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        result = TaskService.delete_task_by_chat_id(self.db, "c1", "task1")
        self.assertTrue(result)
        self.db.delete.assert_called_once_with(mock_task)

    def test_delete_all_tasks_by_chat_id(self):
        """Test deleting all tasks for a chat ID."""
        mock_tasks = [
            MonitoringTask(id=1, chat_id="c1"),
            MonitoringTask(id=2, chat_id="c1"),
        ]
        self.db.query.return_value.filter.return_value.all.return_value = mock_tasks

        result = TaskService.delete_task_by_chat_id(self.db, "c1")
        self.assertTrue(result)
        self.assertEqual(self.db.delete.call_count, 2)

    def test_update_task_graphql_endpoint(self):
        """Test updating only the GraphQL endpoint."""
        mock_task = MagicMock(spec=MonitoringTask)
        mock_task.id = 1
        mock_task.name = "task1"
        mock_task.graphql_endpoint = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        update_data = MonitoringTaskUpdate(
            graphql_endpoint="https://www.olx.pl/apigateway/graphql"
        )

        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task = TaskService.update_task(self.db, 1, update_data)
            self.assertEqual(
                updated_task.graphql_endpoint,
                "https://www.olx.pl/apigateway/graphql",
            )

    def test_update_task_graphql_payload(self):
        """Test updating the GraphQL payload."""
        mock_task = MagicMock(spec=MonitoringTask)
        mock_task.id = 1
        mock_task.graphql_payload = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        payload = {
            "query": "query ListingSearchQuery { ... }",
            "variables": {
                "searchParameters": [
                    {"key": "category_id", "value": "14"},
                    {"key": "city_id", "value": "17871"},
                ]
            },
        }
        update_data = MonitoringTaskUpdate(graphql_payload=payload)

        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task = TaskService.update_task(self.db, 1, update_data)
            self.assertEqual(updated_task.graphql_payload, payload)

    def test_update_task_graphql_headers(self):
        """Test updating the GraphQL headers."""
        mock_task = MagicMock(spec=MonitoringTask)
        mock_task.id = 1
        mock_task.graphql_headers = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "accept-language": "pl",
            "x-client": "DESKTOP",
        }
        update_data = MonitoringTaskUpdate(graphql_headers=headers)

        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task = TaskService.update_task(self.db, 1, update_data)
            self.assertEqual(updated_task.graphql_headers, headers)

    def test_update_task_graphql_captured_at(self):
        """Test updating the GraphQL captured timestamp."""
        mock_task = MagicMock(spec=MonitoringTask)
        mock_task.id = 1
        mock_task.graphql_captured_at = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        captured_at = datetime(2026, 2, 8, 22, 34, 19)
        update_data = MonitoringTaskUpdate(graphql_captured_at=captured_at)

        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task = TaskService.update_task(self.db, 1, update_data)
            self.assertEqual(updated_task.graphql_captured_at, captured_at)

    def test_update_task_all_graphql_fields(self):
        """Test updating all GraphQL fields at once."""
        mock_task = MagicMock(spec=MonitoringTask)
        mock_task.id = 1
        mock_task.name = "task1"
        mock_task.graphql_endpoint = None
        mock_task.graphql_payload = None
        mock_task.graphql_headers = None
        mock_task.graphql_captured_at = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        captured_at = datetime(2026, 2, 8, 22, 34, 19)
        payload = {
            "query": "query ListingSearchQuery { ... }",
            "variables": {"searchParameters": [{"key": "category_id", "value": "14"}]},
        }
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
        }

        update_data = MonitoringTaskUpdate(
            graphql_endpoint="https://www.olx.pl/apigateway/graphql",
            graphql_payload=payload,
            graphql_headers=headers,
            graphql_captured_at=captured_at,
        )

        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task = TaskService.update_task(self.db, 1, update_data)
            self.assertEqual(
                updated_task.graphql_endpoint,
                "https://www.olx.pl/apigateway/graphql",
            )
            self.assertEqual(updated_task.graphql_payload, payload)
            self.assertEqual(updated_task.graphql_headers, headers)
            self.assertEqual(updated_task.graphql_captured_at, captured_at)

    def test_update_task_graphql_fields_with_other_fields(self):
        """Test updating GraphQL fields alongside regular fields."""
        mock_task = MagicMock(spec=MonitoringTask)
        mock_task.id = 1
        mock_task.name = "old_name"
        mock_task.url = "http://old.com"
        mock_task.graphql_endpoint = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        update_data = MonitoringTaskUpdate(
            name="new_name",
            graphql_endpoint="https://www.olx.pl/apigateway/graphql",
        )

        with patch(
            "api.services.task_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            updated_task = TaskService.update_task(self.db, 1, update_data)
            self.assertEqual(updated_task.name, "new_name")
            self.assertEqual(
                updated_task.graphql_endpoint,
                "https://www.olx.pl/apigateway/graphql",
            )


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import app
from core import database as db_mod


def _build_client(db_path: str) -> TestClient:
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_mod.Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_mod.get_db] = override_get_db
    return TestClient(app)


class TestTasksRouter(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.environ.setdefault("DATABASE_URL", "sqlite:///test-router-tasks.db")
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "test.db")
        self.client = _build_client(self.db_path)

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        self.client.close()
        self.tmpdir.cleanup()

    async def test_create_get_update_delete_and_404(self):
        payload = {
            "chat_id": "c1",
            "name": "n1",
            "url": "https://www.olx.pl/d/oferty/q-q/",
        }
        r = self.client.post("/api/v1/tasks/", json=payload)
        self.assertEqual(r.status_code, 201, r.text)
        task = r.json()
        tid = task["id"]

        r2 = self.client.get(f"/api/v1/tasks/{tid}")
        self.assertEqual(r2.status_code, 200)

        ru = self.client.put(f"/api/v1/tasks/{tid}", json={"name": "renamed"})
        self.assertEqual(ru.status_code, 200)
        self.assertEqual(ru.json()["name"], "renamed")

        rd = self.client.delete(f"/api/v1/tasks/{tid}")
        self.assertEqual(rd.status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/tasks/{tid}").status_code, 404)

    async def test_list_by_chat_and_pending_and_delete_by_chat(self):
        for i in range(2):
            self.client.post(
                "/api/v1/tasks/",
                json={
                    "chat_id": "c2",
                    "name": f"n{i}",
                    "url": f"https://www.olx.pl/d/oferty/q-{i}/",
                },
            )
        r = self.client.get("/api/v1/tasks/chat/c2")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["total"], 2)

        rp = self.client.get("/api/v1/tasks/pending")
        self.assertEqual(rp.status_code, 200)
        self.assertGreaterEqual(len(rp.json()["tasks"]), 2)

        self.assertEqual(
            self.client.delete(
                "/api/v1/tasks/chat/c2", params={"name": "n0"}
            ).status_code,
            204,
        )
        self.assertEqual(self.client.delete("/api/v1/tasks/chat/c2").status_code, 204)
        self.assertEqual(self.client.delete("/api/v1/tasks/chat/c2").status_code, 404)

    async def test_create_task_conflict(self):
        payload = {
            "chat_id": "c4",
            "name": "n1",
            "url": "https://www.olx.pl/d/oferty/q-q/",
        }
        r = self.client.post("/api/v1/tasks/", json=payload)
        self.assertEqual(r.status_code, 201, r.text)

        r2 = self.client.post("/api/v1/tasks/", json=payload)
        self.assertEqual(r2.status_code, 400)

    async def test_delete_tasks_by_chat_id_not_found(self):
        r = self.client.delete("/api/v1/tasks/chat/non-existent-chat-id")
        self.assertEqual(r.status_code, 404)

    async def test_update_last_got_item_not_found(self):
        r = self.client.post("/api/v1/tasks/999/update-last-got-item")
        self.assertEqual(r.status_code, 404)

    async def test_get_all_tasks_empty(self):
        r = self.client.get("/api/v1/tasks/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"tasks": [], "total": 0})

    async def test_update_non_existent_task(self):
        r = self.client.put("/api/v1/tasks/999", json={"name": "new_name"})
        self.assertEqual(r.status_code, 404)

    async def test_delete_non_existent_task(self):
        r = self.client.delete("/api/v1/tasks/999")
        self.assertEqual(r.status_code, 404)

    async def test_delete_task_by_chat_id_and_non_existent_name(self):
        self.client.post(
            "/api/v1/tasks/", json={"chat_id": "c5", "name": "n1", "url": "u"}
        )
        r = self.client.delete("/api/v1/tasks/chat/c5", params={"name": "non-existent"})
        self.assertEqual(r.status_code, 404)

    async def test_get_items_to_send_for_non_existent_task(self):
        r = self.client.get("/api/v1/tasks/999/items-to-send")
        self.assertEqual(r.status_code, 404)

    async def test_update_last_got_item_and_items_to_send(self):
        t = self.client.post(
            "/api/v1/tasks/",
            json={
                "chat_id": "c3",
                "name": "n",
                "url": "https://www.olx.pl/d/oferty/q-src/",
            },
        ).json()
        tid = t["id"]

        base_time = datetime(2025, 1, 10, 10, 0, 0)
        with patch(
            "api.services.item_service.now_warsaw",
            lambda: base_time - timedelta(hours=2),
        ):
            self.client.post(
                "/api/v1/items/",
                json={"item_url": "https://www.olx.pl/item/a", "source_url": t["url"]},
            )

        # Update timestamp to a point after item 'a' is created
        with patch(
            "api.services.task_service.now_warsaw",
            lambda: base_time - timedelta(hours=1),
        ):
            self.assertEqual(
                self.client.post(
                    f"/api/v1/tasks/{tid}/update-last-got-item"
                ).status_code,
                200,
            )

        # Create item 'b' after the timestamp update
        with patch(
            "api.services.item_service.now_warsaw",
            lambda: base_time - timedelta(minutes=10),
        ):
            self.client.post(
                "/api/v1/items/",
                json={"item_url": "https://www.olx.pl/item/b", "source_url": t["url"]},
            )

        with patch("api.services.item_service.now_warsaw", lambda: base_time):
            r = self.client.get(f"/api/v1/tasks/{tid}/items-to-send")
            self.assertEqual(r.status_code, 200)
            urls = [it["item_url"] for it in r.json()["items"]]
            self.assertIn("https://www.olx.pl/item/b", urls)
            self.assertNotIn("https://www.olx.pl/item/a", urls)

    async def test_create_task_with_graphql_fields_null(self):
        """Test that newly created tasks have null GraphQL fields."""
        payload = {
            "chat_id": "c_graphql_1",
            "name": "test_graphql",
            "url": "https://www.olx.pl/d/oferty/q-test/",
        }
        r = self.client.post("/api/v1/tasks/", json=payload)
        self.assertEqual(r.status_code, 201)
        task = r.json()

        # GraphQL fields should be null initially
        self.assertIsNone(task.get("graphql_endpoint"))
        self.assertIsNone(task.get("graphql_payload"))
        self.assertIsNone(task.get("graphql_headers"))
        self.assertIsNone(task.get("graphql_captured_at"))

    async def test_update_task_with_graphql_endpoint(self):
        """Test updating a task with GraphQL endpoint."""
        # Create task
        payload = {
            "chat_id": "c_graphql_2",
            "name": "test_graphql_update",
            "url": "https://www.olx.pl/d/oferty/q-test/",
        }
        r = self.client.post("/api/v1/tasks/", json=payload)
        self.assertEqual(r.status_code, 201)
        tid = r.json()["id"]

        # Update with GraphQL endpoint
        update_payload = {"graphql_endpoint": "https://www.olx.pl/apigateway/graphql"}
        r = self.client.put(f"/api/v1/tasks/{tid}", json=update_payload)
        self.assertEqual(r.status_code, 200)
        task = r.json()
        self.assertEqual(
            task["graphql_endpoint"], "https://www.olx.pl/apigateway/graphql"
        )

    async def test_update_task_with_all_graphql_fields(self):
        """Test updating a task with all GraphQL fields."""
        # Create task
        payload = {
            "chat_id": "c_graphql_3",
            "name": "test_graphql_full",
            "url": "https://www.olx.pl/d/oferty/q-test/",
        }
        r = self.client.post("/api/v1/tasks/", json=payload)
        self.assertEqual(r.status_code, 201)
        tid = r.json()["id"]

        # Update with all GraphQL fields
        update_payload = {
            "graphql_endpoint": "https://www.olx.pl/apigateway/graphql",
            "graphql_payload": {
                "query": "query ListingSearchQuery { ... }",
                "variables": {
                    "searchParameters": [
                        {"key": "category_id", "value": "14"},
                        {"key": "city_id", "value": "17871"},
                    ]
                },
            },
            "graphql_headers": {
                "content-type": "application/json",
                "accept": "application/json",
                "accept-language": "pl",
                "x-client": "DESKTOP",
            },
            "graphql_captured_at": "2026-02-08T22:34:19.136000",
        }
        r = self.client.put(f"/api/v1/tasks/{tid}", json=update_payload)
        self.assertEqual(r.status_code, 200)
        task = r.json()

        # Verify all GraphQL fields were updated
        self.assertEqual(
            task["graphql_endpoint"], "https://www.olx.pl/apigateway/graphql"
        )
        self.assertEqual(
            task["graphql_payload"]["query"], "query ListingSearchQuery { ... }"
        )
        self.assertEqual(
            len(task["graphql_payload"]["variables"]["searchParameters"]), 2
        )
        self.assertEqual(task["graphql_headers"]["content-type"], "application/json")
        self.assertEqual(task["graphql_headers"]["x-client"], "DESKTOP")
        self.assertIsNotNone(task["graphql_captured_at"])

    async def test_get_task_with_graphql_fields(self):
        """Test retrieving a task with GraphQL fields."""
        # Create task
        payload = {
            "chat_id": "c_graphql_4",
            "name": "test_graphql_get",
            "url": "https://www.olx.pl/d/oferty/q-test/",
        }
        r = self.client.post("/api/v1/tasks/", json=payload)
        tid = r.json()["id"]

        # Update with GraphQL data
        update_payload = {
            "graphql_endpoint": "https://www.olx.pl/apigateway/graphql",
            "graphql_payload": {"query": "test"},
        }
        self.client.put(f"/api/v1/tasks/{tid}", json=update_payload)

        # Get task and verify GraphQL fields are included
        r = self.client.get(f"/api/v1/tasks/{tid}")
        self.assertEqual(r.status_code, 200)
        task = r.json()
        self.assertEqual(
            task["graphql_endpoint"], "https://www.olx.pl/apigateway/graphql"
        )
        self.assertEqual(task["graphql_payload"]["query"], "test")

    async def test_update_task_graphql_and_regular_fields_together(self):
        """Test updating both GraphQL and regular fields in one request."""
        # Create task
        payload = {
            "chat_id": "c_graphql_5",
            "name": "old_name",
            "url": "https://www.olx.pl/d/oferty/q-test/",
        }
        r = self.client.post("/api/v1/tasks/", json=payload)
        tid = r.json()["id"]

        # Update both regular and GraphQL fields
        update_payload = {
            "name": "new_name",
            "graphql_endpoint": "https://www.olx.pl/apigateway/graphql",
            "graphql_payload": {"query": "test query"},
        }
        r = self.client.put(f"/api/v1/tasks/{tid}", json=update_payload)
        self.assertEqual(r.status_code, 200)
        task = r.json()

        # Verify both types of fields were updated
        self.assertEqual(task["name"], "new_name")
        self.assertEqual(
            task["graphql_endpoint"], "https://www.olx.pl/apigateway/graphql"
        )
        self.assertEqual(task["graphql_payload"]["query"], "test query")

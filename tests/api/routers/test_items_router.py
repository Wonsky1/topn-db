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


class TestItemsRouter(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.environ.setdefault("DATABASE_URL", "sqlite:///test-router-items.db")
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "test.db")
        self.client = _build_client(self.db_path)

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        self.client.close()
        self.tmpdir.cleanup()

    async def test_create_and_get_all_and_by_id_and_by_url(self):
        payload = {
            "item_url": "https://www.olx.pl/item/1",
            "source_url": "https://www.olx.pl/d/oferty/q-foo/",
            "title": "Item 1",
            "price": "100 PLN",
            "location": "Warsaw",
            "created_at_pretty": "today",
            "description": "desc",
        }
        r = self.client.post("/api/v1/items/", json=payload)
        self.assertEqual(r.status_code, 201, r.text)
        item = r.json()
        self.assertEqual(item["source"], "OLX")

        r_all = self.client.get("/api/v1/items/?skip=0&limit=10")
        self.assertEqual(r_all.status_code, 200)
        self.assertEqual(r_all.json()["total"], 1)

        r_by_id = self.client.get(f"/api/v1/items/{item['id']}")
        self.assertEqual(r_by_id.status_code, 200)
        self.assertEqual(r_by_id.json()["item_url"], payload["item_url"])

        r_by_url = self.client.get(f"/api/v1/items/by-url/{payload['item_url']}")
        self.assertEqual(r_by_url.status_code, 200)

    async def test_conflict_on_duplicate_create(self):
        payload = {
            "item_url": "https://www.olx.pl/item/dup",
            "source_url": "https://www.olx.pl/d/oferty/q-bar/",
        }
        self.assertEqual(
            self.client.post("/api/v1/items/", json=payload).status_code, 201
        )
        self.assertEqual(
            self.client.post("/api/v1/items/", json=payload).status_code, 409
        )

    async def test_get_items_by_source_url_and_source(self):
        src = "https://www.olx.pl/d/oferty/q-src/"
        for i in range(2):
            self.client.post(
                "/api/v1/items/",
                json={"item_url": f"https://www.olx.pl/item/{i}", "source_url": src},
            )
        r1 = self.client.get(f"/api/v1/items/by-source?source_url={src}&limit=1")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["total"], 1)

        r2 = self.client.get("/api/v1/items/by-source/OLX?limit=10")
        self.assertEqual(r2.status_code, 200)
        self.assertGreaterEqual(r2.json()["total"], 2)

    async def test_recent_items_and_cleanup_and_delete(self):
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        with patch(
            "api.services.item_service.now_warsaw",
            lambda: base_time - timedelta(hours=5),
        ):
            self.client.post(
                "/api/v1/items/",
                json={
                    "item_url": "https://www.olx.pl/item/old",
                    "source_url": "https://www.olx.pl/d/oferty/q-old/",
                },
            )
        with patch(
            "api.services.item_service.now_warsaw",
            lambda: base_time - timedelta(minutes=30),
        ):
            r = self.client.post(
                "/api/v1/items/",
                json={
                    "item_url": "https://www.olx.pl/item/new",
                    "source_url": "https://www.olx.pl/d/oferty/q-new/",
                },
            )
            new_id = r.json()["id"]

        with patch("api.services.item_service.now_warsaw", lambda: base_time):
            r_recent = self.client.get("/api/v1/items/recent?hours=1&limit=10")
            self.assertEqual(r_recent.status_code, 200)
            urls = [it["item_url"] for it in r_recent.json()["items"]]
            self.assertIn("https://www.olx.pl/item/new", urls)
            self.assertNotIn("https://www.olx.pl/item/old", urls)

            r_cleanup = self.client.delete("/api/v1/items/cleanup/older-than/3")
            self.assertEqual(r_cleanup.status_code, 200)

        # delete by id and 404 after
        self.assertEqual(self.client.delete(f"/api/v1/items/{new_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/items/{new_id}").status_code, 404)

    async def test_not_found_by_id_and_by_url(self):
        self.assertEqual(self.client.get("/api/v1/items/999999").status_code, 404)
        self.assertEqual(
            self.client.get("/api/v1/items/by-url/https://nope").status_code, 404
        )

    async def test_delete_not_found(self):
        r = self.client.delete("/api/v1/items/999999")
        self.assertEqual(r.status_code, 404)

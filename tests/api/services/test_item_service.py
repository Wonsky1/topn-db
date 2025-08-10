from datetime import datetime
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch

from api.services.item_service import ItemService


class TestItemService(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = MagicMock()

    async def asyncTearDown(self):
        pass

    async def test_create_item_auto_source(self):
        with patch(
            "api.services.item_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            item = ItemService.create_item(
                self.db,
                type(
                    "D",
                    (),
                    {
                        "item_url": "https://www.olx.pl/x",
                        "source_url": "s",
                        "title": None,
                        "price": None,
                        "location": None,
                        "created_at": None,
                        "created_at_pretty": None,
                        "image_url": None,
                        "description": None,
                        "source": None,
                    },
                )(),
            )
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
        # auto-detected from URL
        assert item.source == "OLX"

    async def test_create_item_otodom_and_with_source(self):
        # Test otodom auto-detection
        with patch(
            "api.services.item_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            item_otodom = ItemService.create_item(
                self.db,
                type(
                    "D",
                    (),
                    {
                        "item_url": "https://www.otodom.pl/x",
                        "source_url": "s",
                        "title": None,
                        "price": None,
                        "location": None,
                        "created_at": None,
                        "created_at_pretty": None,
                        "image_url": None,
                        "description": None,
                        "source": None,
                    },
                )(),
            )
        assert item_otodom.source == "Otodom"

        # Test with source already provided
        with patch(
            "api.services.item_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            item_with_source = ItemService.create_item(
                self.db,
                type(
                    "D",
                    (),
                    {
                        "item_url": "https://www.olx.pl/y",
                        "source_url": "s",
                        "title": None,
                        "price": None,
                        "location": None,
                        "created_at": None,
                        "created_at_pretty": None,
                        "image_url": None,
                        "description": None,
                        "source": "CustomSource",  # Source is provided
                    },
                )(),
            )
        assert item_with_source.source == "CustomSource"

    async def test_create_item_no_source_detected(self):
        with patch(
            "api.services.item_service.now_warsaw", lambda: datetime(2025, 1, 1)
        ):
            item = ItemService.create_item(
                self.db,
                type(
                    "D",
                    (),
                    {
                        "item_url": "https://www.some-other-site.com/x",
                        "source_url": "s",
                        "title": None,
                        "price": None,
                        "location": None,
                        "created_at": None,
                        "created_at_pretty": None,
                        "image_url": None,
                        "description": None,
                        "source": None,
                    },
                )(),
            )
        assert item.source is None

    async def test_get_item_by_url(self):
        q = self.db.query.return_value
        q.filter.return_value.first.return_value = object()
        res = ItemService.get_item_by_url(self.db, "u")
        assert res is not None

    async def test_get_items_by_source_url(self):
        q = self.db.query.return_value
        q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            1,
            2,
        ]
        res = ItemService.get_items_by_source_url(self.db, "src", limit=1)
        assert res == [1, 2]

    async def test_get_items_by_source(self):
        q = self.db.query.return_value
        q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            1
        ]
        res = ItemService.get_items_by_source(self.db, "OLX", limit=5)
        assert res == [1]

    async def test_get_all_items_and_count(self):
        self.db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            1,
            2,
        ]
        assert ItemService.get_all_items(self.db, 0, 2) == [1, 2]
        self.db.query.return_value.count.return_value = 7
        assert ItemService.get_items_count(self.db) == 7

    async def test_get_items_to_send_for_task_with_last_got_item(self):
        task = type(
            "T", (), {"last_got_item": datetime(2025, 1, 1, 10, 0, 0), "url": "src"}
        )()
        q = self.db.query.return_value
        q.filter.return_value.order_by.return_value.all.return_value = ["a"]
        res = ItemService.get_items_to_send_for_task(self.db, task)
        assert res == ["a"]

    async def test_get_items_to_send_for_task_without_last_got_item_threshold(self):
        task = type("T", (), {"last_got_item": None, "url": "src"})()
        with patch(
            "api.services.item_service.settings.DEFAULT_SENDING_FREQUENCY_MINUTES", 60
        ), patch(
            "api.services.item_service.settings.DEFAULT_LAST_MINUTES_GETTING", 30
        ), patch(
            "api.services.item_service.now_warsaw",
            lambda: datetime(2025, 1, 1, 12, 0, 0),
        ):
            q = self.db.query.return_value
            q.filter.return_value.order_by.return_value.all.return_value = ["b"]
            res = ItemService.get_items_to_send_for_task(self.db, task)
            assert res == ["b"]

    async def test_get_items_to_send_for_task_default_threshold(self):
        task = type("T", (), {"last_got_item": None, "url": "src"})()
        with patch(
            "api.services.item_service.settings.DEFAULT_SENDING_FREQUENCY_MINUTES", 30
        ), patch(
            "api.services.item_service.settings.DEFAULT_LAST_MINUTES_GETTING", 60
        ), patch(
            "api.services.item_service.now_warsaw",
            lambda: datetime(2025, 1, 1, 12, 0, 0),
        ):
            q = self.db.query.return_value
            q.filter.return_value.order_by.return_value.all.return_value = ["c"]
            res = ItemService.get_items_to_send_for_task(self.db, task)
            assert res == ["c"]

    async def test_get_items_to_send_for_task_by_id(self):
        # Test not found
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert ItemService.get_items_to_send_for_task_by_id(self.db, 1) == []

        # Test found
        task = type("T", (), {"last_got_item": None, "url": "src"})()
        self.db.query.return_value.filter.return_value.first.return_value = task
        with patch(
            "api.services.item_service.ItemService.get_items_to_send_for_task"
        ) as mock_get:
            mock_get.return_value = ["item1"]
            res = ItemService.get_items_to_send_for_task_by_id(self.db, 2)
            assert res == ["item1"]
            mock_get.assert_called_once_with(self.db, task)

    async def test_delete_items_older_than_n_days(self):
        with patch(
            "api.services.item_service.now_warsaw",
            lambda: datetime(2025, 1, 10, 0, 0, 0),
        ):
            q = self.db.query.return_value
            q.filter.return_value.all.return_value = [
                type("I", (), {})(),
                type("I", (), {})(),
            ]
            res = ItemService.delete_items_older_than_n_days(self.db, 3)
            assert len(res) == 2
            assert self.db.delete.call_count == 2
            self.db.commit.assert_called_once()

    async def test_delete_item_by_id_true_false(self):
        self.db.query.return_value.filter.return_value.first.return_value = object()
        assert ItemService.delete_item_by_id(self.db, 1) is True
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert ItemService.delete_item_by_id(self.db, 1) is False

    async def test_get_recent_items(self):
        with patch(
            "api.services.item_service.now_warsaw",
            lambda: datetime(2025, 1, 1, 12, 0, 0),
        ):
            q = self.db.query.return_value
            q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
                1
            ]
            assert ItemService.get_recent_items(self.db, hours=1, limit=10) == [1]

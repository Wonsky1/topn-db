from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from api.services.city_service import CityService


class TestCityService(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = MagicMock()

    async def asyncTearDown(self):
        pass

    async def test_get_all_cities(self):
        """Test getting all cities."""
        self.db.query.return_value.order_by.return_value.all.return_value = [
            "city1",
            "city2",
        ]
        result = CityService.get_all_cities(self.db)
        assert result == ["city1", "city2"]

    async def test_get_city_by_id_found(self):
        """Test getting city by ID when found."""
        mock_city = type("City", (), {"id": 1, "name_raw": "Warszawa"})()
        self.db.query.return_value.filter.return_value.first.return_value = mock_city
        result = CityService.get_city_by_id(self.db, 1)
        assert result == mock_city

    async def test_get_city_by_id_not_found(self):
        """Test getting city by ID when not found."""
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = CityService.get_city_by_id(self.db, 999)
        assert result is None

    async def test_get_city_by_normalized_name_found(self):
        """Test getting city by normalized name when found."""
        mock_city = type("City", (), {"id": 1, "name_normalized": "warszawa"})()
        self.db.query.return_value.filter.return_value.first.return_value = mock_city
        result = CityService.get_city_by_normalized_name(self.db, "warszawa")
        assert result == mock_city

    async def test_get_city_by_normalized_name_not_found(self):
        """Test getting city by normalized name when not found."""
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = CityService.get_city_by_normalized_name(self.db, "nonexistent")
        assert result is None

    async def test_create_city_success(self):
        """Test creating a new city successfully."""
        # Mock that city doesn't exist
        self.db.query.return_value.filter.return_value.first.return_value = None

        city_data = type(
            "CityCreate", (), {"name_raw": "Warszawa", "name_normalized": "warszawa"}
        )()

        result = CityService.create_city(self.db, city_data)

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
        assert result.name_raw == "Warszawa"
        assert result.name_normalized == "warszawa"

    async def test_create_city_duplicate(self):
        """Test creating a city that already exists."""
        # Mock that city already exists
        existing_city = type("City", (), {"id": 1, "name_normalized": "warszawa"})()
        self.db.query.return_value.filter.return_value.first.return_value = (
            existing_city
        )

        city_data = type(
            "CityCreate", (), {"name_raw": "Warszawa", "name_normalized": "warszawa"}
        )()

        try:
            CityService.create_city(self.db, city_data)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "already exists" in str(e)

    async def test_update_city_success(self):
        """Test updating a city successfully."""
        mock_city = type(
            "City", (), {"id": 1, "name_raw": "Warszawa", "name_normalized": "warszawa"}
        )()

        # Mock get_city_by_id to return the city
        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_city,  # First call for get_city_by_id
            None,  # Second call for checking normalized name conflict
        ]

        city_data = type(
            "CityUpdate",
            (),
            {"name_raw": "Warsaw", "name_normalized": "warsaw"},
        )()

        result = CityService.update_city(self.db, 1, city_data)

        assert result.name_raw == "Warsaw"
        assert result.name_normalized == "warsaw"
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    async def test_update_city_not_found(self):
        """Test updating a city that doesn't exist."""
        self.db.query.return_value.filter.return_value.first.return_value = None

        city_data = type(
            "CityUpdate", (), {"name_raw": "Warsaw", "name_normalized": None}
        )()

        result = CityService.update_city(self.db, 999, city_data)
        assert result is None

    async def test_update_city_normalized_name_conflict(self):
        """Test updating city with conflicting normalized name."""
        mock_city = type(
            "City", (), {"id": 1, "name_raw": "Warszawa", "name_normalized": "warszawa"}
        )()
        conflicting_city = type("City", (), {"id": 2, "name_normalized": "krakow"})()

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_city,  # First call for get_city_by_id
            conflicting_city,  # Second call for checking normalized name conflict
        ]

        city_data = type(
            "CityUpdate", (), {"name_raw": None, "name_normalized": "krakow"}
        )()

        try:
            CityService.update_city(self.db, 1, city_data)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "already exists" in str(e)

    async def test_delete_city_success(self):
        """Test deleting a city successfully."""
        mock_city = type("City", (), {"id": 1})()
        self.db.query.return_value.filter.return_value.first.return_value = mock_city

        result = CityService.delete_city_by_id(self.db, 1)

        assert result is True
        self.db.delete.assert_called_once_with(mock_city)
        self.db.commit.assert_called_once()

    async def test_delete_city_not_found(self):
        """Test deleting a city that doesn't exist."""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = CityService.delete_city_by_id(self.db, 999)

        assert result is False
        self.db.delete.assert_not_called()

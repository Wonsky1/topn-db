from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from api.services.district_service import DistrictService


class TestDistrictService(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = MagicMock()

    async def asyncTearDown(self):
        pass

    async def test_get_all_districts(self):
        """Test getting all districts."""
        self.db.query.return_value.order_by.return_value.all.return_value = [
            "district1",
            "district2",
        ]
        result = DistrictService.get_all_districts(self.db)
        assert result == ["district1", "district2"]

    async def test_get_district_by_id_found(self):
        """Test getting district by ID when found."""
        mock_district = type("District", (), {"id": 1, "name_raw": "Mokotów"})()
        self.db.query.return_value.filter.return_value.first.return_value = (
            mock_district
        )
        result = DistrictService.get_district_by_id(self.db, 1)
        assert result == mock_district

    async def test_get_district_by_id_not_found(self):
        """Test getting district by ID when not found."""
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = DistrictService.get_district_by_id(self.db, 999)
        assert result is None

    async def test_get_districts_by_city_id(self):
        """Test getting all districts for a city."""
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            "district1",
            "district2",
        ]
        result = DistrictService.get_districts_by_city_id(self.db, 1)
        assert result == ["district1", "district2"]

    async def test_create_district_success(self):
        """Test creating a new district successfully."""
        # Mock that district doesn't exist
        self.db.query.return_value.filter.return_value.first.return_value = None

        district_data = type(
            "DistrictCreate",
            (),
            {"city_id": 1, "name_raw": "Mokotów", "name_normalized": "mokotow"},
        )()

        result = DistrictService.create_district(self.db, district_data)

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
        assert result.city_id == 1
        assert result.name_raw == "Mokotów"
        assert result.name_normalized == "mokotow"

    async def test_create_district_duplicate(self):
        """Test creating a district that already exists in the city."""
        # Mock that district already exists
        existing_district = type(
            "District", (), {"id": 1, "city_id": 1, "name_normalized": "mokotow"}
        )()
        self.db.query.return_value.filter.return_value.first.return_value = (
            existing_district
        )

        district_data = type(
            "DistrictCreate",
            (),
            {"city_id": 1, "name_raw": "Mokotów", "name_normalized": "mokotow"},
        )()

        try:
            DistrictService.create_district(self.db, district_data)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "already exists" in str(e)

    async def test_update_district_success(self):
        """Test updating a district successfully."""
        mock_district = type(
            "District",
            (),
            {
                "id": 1,
                "city_id": 1,
                "name_raw": "Mokotów",
                "name_normalized": "mokotow",
            },
        )()

        # Mock get_district_by_id to return the district
        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_district,  # First call for get_district_by_id
            None,  # Second call for checking normalized name conflict
        ]

        district_data = type(
            "DistrictUpdate",
            (),
            {"city_id": None, "name_raw": "Mokotow", "name_normalized": "mokotow"},
        )()

        result = DistrictService.update_district(self.db, 1, district_data)

        assert result.name_raw == "Mokotow"
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    async def test_update_district_not_found(self):
        """Test updating a district that doesn't exist."""
        self.db.query.return_value.filter.return_value.first.return_value = None

        district_data = type(
            "DistrictUpdate",
            (),
            {"city_id": None, "name_raw": "Test", "name_normalized": None},
        )()

        result = DistrictService.update_district(self.db, 999, district_data)
        assert result is None

    async def test_update_district_normalized_name_conflict(self):
        """Test updating district with conflicting normalized name in same city."""
        mock_district = type(
            "District",
            (),
            {
                "id": 1,
                "city_id": 1,
                "name_raw": "Mokotów",
                "name_normalized": "mokotow",
            },
        )()
        conflicting_district = type(
            "District", (), {"id": 2, "city_id": 1, "name_normalized": "srodmiescie"}
        )()

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_district,  # First call for get_district_by_id
            conflicting_district,  # Second call for checking normalized name conflict
        ]

        district_data = type(
            "DistrictUpdate",
            (),
            {"city_id": None, "name_raw": None, "name_normalized": "srodmiescie"},
        )()

        try:
            DistrictService.update_district(self.db, 1, district_data)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "already exists" in str(e)

    async def test_update_district_with_city_change(self):
        """Test updating district and changing its city."""
        mock_district = type(
            "District",
            (),
            {
                "id": 1,
                "city_id": 1,
                "name_raw": "Mokotów",
                "name_normalized": "mokotow",
            },
        )()

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_district,  # First call for get_district_by_id
            None,  # Second call for checking normalized name conflict
        ]

        district_data = type(
            "DistrictUpdate",
            (),
            {"city_id": 2, "name_raw": None, "name_normalized": "mokotow"},
        )()

        result = DistrictService.update_district(self.db, 1, district_data)

        assert result.city_id == 2
        self.db.commit.assert_called_once()

    async def test_delete_district_success(self):
        """Test deleting a district successfully."""
        mock_district = type("District", (), {"id": 1})()
        self.db.query.return_value.filter.return_value.first.return_value = (
            mock_district
        )

        result = DistrictService.delete_district_by_id(self.db, 1)

        assert result is True
        self.db.delete.assert_called_once_with(mock_district)
        self.db.commit.assert_called_once()

    async def test_delete_district_not_found(self):
        """Test deleting a district that doesn't exist."""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = DistrictService.delete_district_by_id(self.db, 999)

        assert result is False
        self.db.delete.assert_not_called()

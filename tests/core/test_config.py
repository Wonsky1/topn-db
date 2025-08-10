import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from core.config import Settings


class TestConfig(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_database_url_raises_error(self):
        # Temporarily override model_config to prevent loading from .env
        original_config = Settings.model_config
        Settings.model_config = SettingsConfigDict(env_file=None, case_sensitive=False)

        with self.assertRaises(ValidationError):
            Settings()  # This should now fail as DATABASE_URL is not in env

        # Restore original config
        Settings.model_config = original_config

    def test_empty_database_url_raises_error(self):
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            with self.assertRaises(ValueError) as cm:
                Settings()
            self.assertIn("DATABASE_URL is required", str(cm.exception))

    def test_settings_load_correctly(self):
        # Make sure settings load without error when env is set
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"}):
            settings = Settings()
            self.assertEqual(settings.DATABASE_URL, "sqlite:///test.db")
            self.assertEqual(settings.DEFAULT_SENDING_FREQUENCY_MINUTES, 1)
            self.assertEqual(settings.DEFAULT_LAST_MINUTES_GETTING, 60)


if __name__ == "__main__":
    unittest.main()

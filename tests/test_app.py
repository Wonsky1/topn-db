import logging

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "olx-database-api"}


def test_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "OLX Database API is running"}


def test_lifespan(caplog):
    """Test the application lifespan events."""
    with caplog.at_level(logging.INFO):
        with TestClient(app):
            pass
    assert "Starting OLX Database API..." in caplog.text
    assert "Database initialized" in caplog.text
    assert "Shutting down OLX Database API..." in caplog.text

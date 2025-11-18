from fastapi.testclient import TestClient

from app.main import app
from app import routes

client = TestClient(app)


def test_sf_status_returns_mocked_data(monkeypatch):
    expected = {
        "org": "Sandbox",
        "contacts_count": 123,
        "status": "ok",
    }

    # Replace the get_status method in the global sf_client with fake one
    monkeypatch.setattr(routes.sf_client, "get_status", lambda: expected)

    response = client.get("/sf-status")
    assert response.status_code == 200
    assert response.json() == expected

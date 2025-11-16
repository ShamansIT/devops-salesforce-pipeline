from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_tasks_status_code():
    response = client.get("/api/tasks")
    assert response.status_code == 200


def test_tasks_response_structure():
    response = client.get("/api/tasks")
    data = response.json()

    # Is list not empty
    assert isinstance(data, list)
    assert len(data) >= 1

    first = data[0]
    # Is keys that we expect are there
    for key in ("id", "title", "description", "status"):
        assert key in first

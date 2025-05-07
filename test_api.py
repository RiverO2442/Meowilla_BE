import pytest
from flask import json
from main import app 

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def test_register_user(client):
    # Simulate a registration POST request
    response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass"
    })
    data = response.get_json()

    assert response.status_code in [201, 400]  # could be 400 if email already exists
    assert "message" in data

def test_search_images(client, monkeypatch):
    # Mock the OpenverseClient.search_images method
    def mock_search_images(query, page, page_size, tags):
        return {"results": [{"id": "123", "title": "Mock Sunset"}]}

    from main import ov_client
    monkeypatch.setattr(ov_client, "search_images", mock_search_images)

    response = client.get("/images?q=sunset")
    data = response.get_json()

    assert response.status_code == 200
    assert "results" in data
    assert data["results"][0]["title"] == "Mock Sunset"

import pytest
from flask import json
from main import app
from config import db  # import db from your config.py

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # in-memory DB for testing
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()  # ✅ Create tables before tests

    with app.test_client() as client:
        yield client

    # Optional: Clean up after tests
    with app.app_context():
        db.drop_all()

def test_register_user(client):
    response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass"
    })
    data = response.get_json()

    assert response.status_code in [201, 400]  # 400 if user/email already exists
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

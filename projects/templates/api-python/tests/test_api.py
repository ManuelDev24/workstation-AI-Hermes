from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_health():
    assert c.get("/health").json() == {"status": "ok"}


def test_create_valid_and_list():
    assert c.post("/items", json={"name": "a", "price": 2.5}).status_code == 201
    assert {"name": "a", "price": 2.5} in c.get("/items").json()


def test_invalid_input_rejected():
    assert c.post("/items", json={"name": "", "price": -1}).status_code == 422

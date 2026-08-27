import pytest
from fastapi.testclient import TestClient

from app import app


def test_cors_allowed_origin():
    client = TestClient(app)
    response = client.get(
        "/api/strategies",
        headers={"Origin": "http://localhost:8000"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallowed_origin():
    client = TestClient(app)
    response = client.get(
        "/api/strategies",
        headers={"Origin": "https://malicious-site.com"}
    )
    assert response.status_code == 200
    # Disallowed origin should not get access-control-allow-origin back
    assert response.headers.get("access-control-allow-origin") is None

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_cors_configuration():
    response = client.options("/api/strategies", headers={
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"
    # Credentials should not be allowed with wildcard origins
    assert response.headers.get("access-control-allow-credentials") is None or response.headers.get("access-control-allow-credentials") == "false"

def test_get_strategies_endpoint():
    response = client.get("/api/strategies")
    assert response.status_code == 200
    data = response.json()
    assert "strategies" in data
    assert "sma_crossover" in data["strategies"]

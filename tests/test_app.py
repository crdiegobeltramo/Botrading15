from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_strategies_endpoint():
    response = client.get("/api/strategies")
    assert response.status_code == 200
    data = response.json()
    assert "strategies" in data
    assert "sma_crossover" in data["strategies"]


def test_cors_headers():
    response = client.options(
        "/api/strategies",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    # Credentials should NOT be allowed for wildcard origins
    assert response.headers.get("access-control-allow-credentials") is None or response.headers.get("access-control-allow-credentials") == "false"


def test_static_files():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_error_handling_sanitization(monkeypatch):
    # Test that user validation errors return 400 with message
    def mock_fetch_klines_val_error(*args, **kwargs):
        raise ValueError("Intervalo no soportado: 1h")

    import app as app_module
    monkeypatch.setattr(app_module, "fetch_klines", mock_fetch_klines_val_error)

    payload = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "start": "2023-01-01",
        "end": "2023-01-02",
        "strategy": "sma_crossover",
    }
    response = client.post("/api/backtest", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Intervalo no soportado: 1h"

    # Test that internal runtime exceptions return 500 and do not leak internal stack/secret details
    def mock_unexpected_error(*args, **kwargs):
        raise RuntimeError("Binance secret key connection failed at internal_db.py:42")

    monkeypatch.setattr(app_module, "fetch_klines", mock_unexpected_error)
    response = client.post("/api/backtest", json=payload)
    assert response.status_code == 500
    # Detail must be sanitized and not leak internal exception details
    assert response.json()["detail"] == "An error occurred processing the request"

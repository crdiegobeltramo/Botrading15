from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

from app import app

client = TestClient(app)


def test_backtest_error_handling_sanitization():
    # Simular una excepción interna imprevista al obtener klines
    with patch("app.fetch_klines", side_effect=RuntimeError("Sensitive database connection details: postgres://user:secret@localhost:5432/db")):
        payload = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "start": "2023-01-01",
            "end": "2023-01-02",
            "strategy": "sma_crossover"
        }
        response = client.post("/api/backtest", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Operation failed"
        assert "postgres" not in response.text
        assert "secret" not in response.text


def test_live_signal_error_handling_sanitization():
    with patch("app.fetch_klines", side_effect=Exception("Internal API key leaked: secret_12345")):
        payload = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "strategy": "sma_crossover"
        }
        response = client.post("/api/live/signal", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Operation failed"
        assert "secret_12345" not in response.text


def test_value_error_handling():
    with patch("app.fetch_klines", side_effect=ValueError("Intervalo no soportado: 2m")):
        payload = {
            "symbol": "BTCUSDT",
            "interval": "2m",
            "start": "2023-01-01",
            "end": "2023-01-02",
            "strategy": "sma_crossover"
        }
        response = client.post("/api/backtest", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Intervalo no soportado: 2m"

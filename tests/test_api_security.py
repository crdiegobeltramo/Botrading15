import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_backtest_invalid_symbol():
    payload = {
        "symbol": "BTCUSDT; DROP TABLE users;--",
        "interval": "1d",
        "start": "2023-01-01",
        "end": "2023-01-10",
        "strategy": "sma_crossover",
        "source": "binance"
    }
    response = client.post("/api/backtest", json=payload)
    assert response.status_code == 422

def test_backtest_invalid_interval():
    payload = {
        "symbol": "BTCUSDT",
        "interval": "invalid_interval",
        "start": "2023-01-01",
        "end": "2023-01-10",
        "strategy": "sma_crossover",
        "source": "binance"
    }
    response = client.post("/api/backtest", json=payload)
    assert response.status_code == 422

def test_live_signal_invalid_lookback():
    payload = {
        "symbol": "BTCUSDT",
        "interval": "1d",
        "strategy": "sma_crossover",
        "source": "binance",
        "lookback_days": 100000  # DoS risk exceeded
    }
    response = client.post("/api/live/signal", json=payload)
    assert response.status_code == 422

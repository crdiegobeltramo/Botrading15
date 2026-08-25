import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app import app

class TestAppSecurityAndAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_strategies(self):
        response = self.client.get("/api/strategies")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("strategies", json_data)
        self.assertIn("sma_crossover", json_data["strategies"])
        self.assertIn("bbands", json_data["strategies"])

    def test_static_web_ui(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("html", response.headers.get("content-type", "").lower())

    @patch("app.fetch_klines")
    def test_error_detail_sanitization(self, mock_fetch):
        # Simulate internal failure with sensitive details (e.g. database/API connection credentials)
        mock_fetch.side_effect = Exception("Sensitive connection error details: user=admin secret=12345")

        payload = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "start": "2023-01-01",
            "end": "2023-01-02",
            "strategy": "sma_crossover",
            "source": "binance",
        }
        response = self.client.post("/api/backtest", json=payload)
        self.assertEqual(response.status_code, 400)
        json_data = response.json()
        # Verify sensitive internal error message is NOT exposed to client
        self.assertNotIn("user=admin secret=12345", json_data["detail"])
        self.assertEqual(json_data["detail"], "An error occurred while processing the backtest request")

import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app


class TestAppSecurityAndEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_static_files_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<title>Trading Bot UI</title>", response.text)

    def test_get_strategies_endpoint(self):
        response = self.client.get("/api/strategies")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("strategies", data)
        self.assertIn("sma_crossover", data["strategies"])

    def test_cors_security_headers(self):
        # OPTIONS request preflight check
        response = self.client.options(
            "/api/strategies",
            headers={"Origin": "https://example.com", "Access-Control-Request-Method": "GET"},
        )
        # Should NOT contain access-control-allow-credentials: true when allow_origins is '*'
        self.assertNotIn("access-control-allow-credentials", response.headers)

    @patch("app.fetch_klines")
    def test_backtest_error_handling_sanitizes_stack_trace(self, mock_fetch):
        # Simulate unexpected internal server / library exception with internal details
        mock_fetch.side_effect = RuntimeError("Internal db connection password=secret123 failed!")

        payload = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "start": "2023-01-01",
            "end": "2023-01-02",
            "strategy": "sma_crossover",
            "source": "binance",
            "initial_capital": 1000,
            "fee": 0.001,
            "fast": 10,
            "slow": 30,
        }

        response = self.client.post("/api/backtest", json=payload)
        self.assertEqual(response.status_code, 400)
        detail = response.json().get("detail", "")
        # Confirm internal secrets or stack info are not leaked
        self.assertNotIn("password=secret123", detail)
        self.assertEqual(detail, "Error occurred while processing backtest")


if __name__ == "__main__":
    unittest.main()

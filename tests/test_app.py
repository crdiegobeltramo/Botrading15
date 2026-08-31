import unittest
from fastapi.testclient import TestClient
from app import app


class TestAppSecurityAndEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_cors_headers(self):
        # Test OPTIONS preflight request
        response = self.client.options(
            "/api/strategies",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "*")
        # Ensure allow-credentials is not set to true for wildcard origins
        self.assertNotIn("access-control-allow-credentials", response.headers)

    def test_get_strategies_endpoint(self):
        response = self.client.get("/api/strategies")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("strategies", data)
        self.assertIn("sma_crossover", data["strategies"])
        self.assertIn("bbands", data["strategies"])

    def test_static_files_serving(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))


if __name__ == "__main__":
    unittest.main()

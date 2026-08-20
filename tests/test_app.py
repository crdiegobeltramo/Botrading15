import unittest
from fastapi.testclient import TestClient
from app import app


class TestAppSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_static_files_serve(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_cors_middleware_config(self):
        # Verify CORS headers on preflight OPTIONS request
        response = self.client.options(
            "/api/strategies",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(response.status_code, 200)
        # Verify allow_credentials is not set to true when origins is wildcard
        self.assertNotIn("access-control-allow-credentials", response.headers)

    def test_get_strategies_endpoint(self):
        response = self.client.get("/api/strategies")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("strategies", data)
        self.assertIn("sma_crossover", data["strategies"])


if __name__ == "__main__":
    unittest.main()

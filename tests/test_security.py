import unittest
from fastapi.testclient import TestClient

from app import app


class TestSecurityCORS(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_cors_headers_allowed_origin(self):
        # Test preflight request with an allowed origin
        response = self.client.options(
            "/api/strategies",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:8000")
        self.assertEqual(response.headers.get("access-control-allow-credentials"), "true")

    def test_cors_headers_disallowed_origin(self):
        # Test preflight request with a disallowed untrusted origin
        response = self.client.options(
            "/api/strategies",
            headers={
                "Origin": "https://malicious-website.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Fastapi CORSMiddleware will not echo untrusted origin in access-control-allow-origin
        self.assertNotEqual(response.headers.get("access-control-allow-origin"), "https://malicious-website.com")
        self.assertNotEqual(response.headers.get("access-control-allow-origin"), "*")


if __name__ == "__main__":
    unittest.main()

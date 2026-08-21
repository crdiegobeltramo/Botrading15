import unittest
from fastapi.testclient import TestClient
from app import app


class TestAppSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_security_headers_present(self):
        response = self.client.get("/api/strategies")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")

    def test_cors_credentials_not_allowed(self):
        # OPTIONS preflight check or response headers
        response = self.client.options(
            "/api/strategies",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Verify Access-Control-Allow-Credentials is not true or not present
        allow_cred = response.headers.get("access-control-allow-credentials")
        self.assertNotEqual(allow_cred, "true")


if __name__ == "__main__":
    unittest.main()

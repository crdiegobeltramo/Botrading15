import unittest
from fastapi.testclient import TestClient
from app import app


class TestCorsSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_cors_credentials_disabled_for_wildcard_origins(self):
        # Request with Origin header
        response = self.client.get(
            "/api/strategies",
            headers={"Origin": "https://example.com"}
        )
        self.assertEqual(response.status_code, 200)
        # Verify Access-Control-Allow-Credentials is not set to 'true'
        credentials_header = response.headers.get("access-control-allow-credentials")
        self.assertNotEqual(
            credentials_header,
            "true",
            "Access-Control-Allow-Credentials should not be true when using wildcard allow_origins"
        )

    def test_cors_options_preflight(self):
        response = self.client.options(
            "/api/strategies",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        self.assertEqual(response.status_code, 200)
        credentials_header = response.headers.get("access-control-allow-credentials")
        self.assertNotEqual(
            credentials_header,
            "true",
            "Access-Control-Allow-Credentials should not be true in preflight when using wildcard allow_origins"
        )


if __name__ == "__main__":
    unittest.main()

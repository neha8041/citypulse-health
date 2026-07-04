import unittest
from fastapi.testclient import TestClient

from app.main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "CityPulse Health API is running securely."})

if __name__ == "__main__":
    unittest.main()

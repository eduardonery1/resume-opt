import os
import unittest
import uuid

from dotenv import load_dotenv
from fastapi.testclient import TestClient

from api.main import app

load_dotenv()


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.token = os.getenv('DEBUG_TOKEN')
        self.client = TestClient(app)

    def test_auth_get(self):
        response = self.client.get("/auth")
        self.assertEqual(response.status_code, 200)

        token = response.json()["auth"]
        self.assertIsInstance(uuid.UUID(token, version=4), uuid.UUID)


if __name__ == '__main__':
    unittest.main()

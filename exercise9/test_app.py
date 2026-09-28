import unittest

from app import app


class AppTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_status_code(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_text(self):
        response = self.client.get('/')
        self.assertIn(b"Hello, Jenkins Multi-Stage Pipeline!", response.data)


if __name__ == '__main__':
    unittest.main()

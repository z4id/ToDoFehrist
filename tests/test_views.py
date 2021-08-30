from django.test import TestCase


class TestAppUserLogin(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        pass

    def test_invalid_email_address(self):
        self.assertTrue(True)
"""
    Contains unit tests to test todofehrist app's views
    ===================================================
"""
import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from todofehrist.enums import UserSubscriptionTypesEnum
from todofehrist.models import AppUser, UserSubscriptionType, AppUserLogin


class SignupTest(APITestCase):
    """
        Contains unit tests for register route (Sing up process by email)
    """

    @classmethod
    def setUpClass(cls):
        """
        This method is inherited by APITestCase Class,
        used to setup basic/common variables across
        all test cases
        """

        super().setUpClass()
        cls.client = APIClient()
        cls.register_url = reverse('register')

    def setUp(self):
        pass

    def test_invalid_email_address(self):
        """
        This method tests register view with invalid email address.
        """

        signup_dict = {"email": "my_invalid_email_address.com", "password": "my_password"}

        response = self.client.post(self.register_url, signup_dict)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data.get("email", None), ["Enter a valid email address."])

    def test_valid_email_address(self):
        """
        This method contains test for register view with a valid email address.
        """

        signup_dict = {"email": "abc@gmail.com", "password": "my_password"}

        response = self.client.post(self.register_url, signup_dict)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(True if signup_dict['email'] in response_data.get("msg", '') else False)


class LoginTest(APITestCase):
    """
        Contains unit tests for auth route (Sing up process by email)
    """

    @classmethod
    def setUpClass(cls):
        """
        This method is inherited by APITestCase Class,
        used to setup basic/common variables across
        all test cases
        """

        super().setUpClass()
        cls.client = APIClient()
        cls.login_url = reverse('login')
        cls.login_credentials = {"email": "valid_email@gmail.com", "password": "my_password"}

    def setUp(self):
        app_user = AppUser(email=self.login_credentials["email"])
        app_user.set_password(self.login_credentials["password"])

        user_subscription_type = UserSubscriptionType.objects.get_or_create(
            name=UserSubscriptionTypesEnum.FREEMIUM.value)[0]
        app_user.user_subscription_type = user_subscription_type

        app_user.is_email_verified = True

        app_user.save()

        self.app_user = app_user

    def test_invalid_credentials(self):
        """
        This method contains test for auth view with an invalid email address.
        """

        login_dict = {"email": "invalid_email@gmail.com", "password": "my_password"}

        response = self.client.post(self.login_url, login_dict)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data.get("msg", None), "Email Address doesn't exist.")

    def test_valid_credentials(self):
        """
        This method contains test for auth view with a valid email/password combination.
        """

        login_dict = {"email": "valid_email@gmail.com", "password": "my_password"}

        response = self.client.post(self.login_url, login_dict)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_token = AppUserLogin.objects.get(user=self.app_user.id).token
        self.assertEqual(response_data["token"], expected_token)

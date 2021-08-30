from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
import json

from todofehrist.models import AppUser, UserSubscriptionType, AppUserLogin
from todofehrist.enums import UserSubscriptionTypesEnum


class SignupTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.register_url = reverse('register')

    def setUp(self):
        pass

    def test_invalid_email_address(self):

        signup_dict = {"email": "my_invalid_email_address.com", "password": "my_password"}

        response = self.client.post(self.register_url, signup_dict)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data.get("email", None), ["Enter a valid email address."])

    def test_valid_email_address(self):

        signup_dict = {"email": "abc@gmail.com", "password": "my_password"}

        response = self.client.post(self.register_url, signup_dict)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(True if signup_dict['email'] in response_data.get("msg", '') else False)


class LoginTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.login_url = reverse('login')
        cls.login_credentials = {"email": "valid_email@gmail.com", "password": "my_password"}

    def setUp(self):
        app_user = AppUser(email=self.login_credentials["email"])
        app_user.set_password(self.login_credentials["password"])

        user_subscription_type = UserSubscriptionType.objects.get_or_create(
            name=UserSubscriptionTypesEnum.Freemium.value)[0]
        app_user.user_subscription_type = user_subscription_type

        app_user.is_email_verified = True

        app_user.save()

        self.app_user = app_user

    def test_invalid_credentials(self):

        login_dict = {"email": "invalid_email@gmail.com", "password": "my_password"}

        response = self.client.post(self.login_url, login_dict)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data.get("msg", None), "Email Address doesn't exist.")

    def test_valid_credentials(self):

        login_dict = {"email": "valid_email@gmail.com", "password": "my_password"}

        response = self.client.post(self.login_url, login_dict)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["token"], AppUserLogin.objects.get(user=self.app_user.id).token)

"""
NAME
    todofehrist.models.py

DESCRIPTION
    Contains all models for todofehrist application

AUTHOR
    Zaid Afzal
"""
import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from todofehrist.enums import UserSubscriptionTypesEnum


class UserSubscriptionType(models.Model):
    """
    NAME
        UserSubscriptionType

    DESCRIPTION
        Custom Django Model for SubscriptionType of User.
    """
    name = models.CharField(max_length=30, unique=True, null=False)
    price = models.IntegerField(default=0, null=False)
    currency = models.CharField(max_length=20, default='USD')


class AppUser(AbstractUser):
    """
        NAME
            AppUser

        DESCRIPTION
            Custom Django Model for User.
    """

    is_staff = None
    is_superuser = None

    user_subscription_type = models.ForeignKey(UserSubscriptionType, on_delete=models.CASCADE)
    is_email_verified = models.BooleanField(default=False)
    is_oauth = models.BooleanField(default=False)
    updated_datetime = models.DateTimeField(null=True)

    class Meta:
        """
        NAME
            Meta

        DESCRIPTION

        """
        db_table = 'AppUser'

    class AppUserManager(BaseUserManager):
        """
        NAME
            AppUserManager

        DESCRIPTION

        """

        def create_app_user(self, email_address=None, password=None):
            """
            This method creates an object of AppUser when validated data provided
            from Models' serializer.
            """
            if not email_address or not password:
                raise ValueError("Empty Signup Credentials.")

            result_ = UserSubscriptionType.objects.get_or_create(
                        name=UserSubscriptionTypesEnum.FREEMIUM.value)
            user_subscription_type = result_[0]

            email_address = self.normalize_email(email_address)
            app_user = self.model(email=email_address, username=email_address)
            app_user.set_password(password)
            app_user.user_subscription_type = user_subscription_type
            app_user.save()

            return app_user

        def create_app_user_via_oauth(self, email_address=None):
            """
            This method creates an object of AppUser when validated data provided
            from Models' serializer.
            """
            if not email_address:
                raise ValueError("Empty Signup Credentials.")

            result_ = UserSubscriptionType.objects.get_or_create(
                        name=UserSubscriptionTypesEnum.FREEMIUM.value)
            user_subscription_type = result_[0]

            app_user = self.model(email=email_address, username=email_address)
            app_user.user_subscription_type = user_subscription_type
            app_user.is_oauth = True
            app_user.is_email_verified = True
            app_user.save()

            return app_user

    objects = AppUserManager()


class AppUserLogin(models.Model):
    """
    NAME
        AppUserLogin

    DESCRIPTION
        Custom Django Model for Login/Auth handling of AppUser.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, unique=True)
    token = models.CharField(max_length=256, null=False)
    created_at = models.DateTimeField(default=datetime.datetime.utcnow())
    expire_at = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        """
        This method sets login/auth token's expiry datetime using created_at
        & and time margin to expire set in projects setting.py
        """
        # self.expire_at = self.created_at
        # self.expire_at = self.created_at + settings.LOGIN_TOKEN_EXPIRY_TIME.seconds
        super(AppUserLogin, self).save(*args, **kwargs)

    class Meta:
        """
        NAME
            Meta

        DESCRIPTION

        """
        db_table = 'AppUserLogin'


class UserQuotaManagement(models.Model):
    """
    NAME
        UserQuotaManagement

    DESCRIPTION
        Custom Django Model for logging application usage for AppUser.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    total_tasks = models.IntegerField(default=0)
    downloaded_file_count = models.IntegerField(default=0)
    last_downloaded_datetime = models.DateTimeField(null=True)
    uploaded_files_count = models.IntegerField(default=0)
    last_uploaded_datetime = models.DateTimeField(null=True)


class UserSubscriptionLimits(models.Model):
    """
    NAME
        UserSubscriptionLimits

    DESCRIPTION

    """
    user_subscription_type = models.ForeignKey(UserSubscriptionType,
                                               on_delete=models.CASCADE, null=False)
    max_allowed_tasks = models.IntegerField(default=0)
    max_allowed_files = models.IntegerField(default=0)
    allowed_files_per_task = models.IntegerField(default=0)
    max_file_size = models.IntegerField(default=0)
    max_downloads_per_day = models.IntegerField(default=0)
    max_uploads_per_day = models.IntegerField(default=0)
    permanent_deletion_time = models.IntegerField(default=0)  # seconds


class Task(models.Model):
    """
    NAME
        Task

    DESCRIPTION

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    title = models.CharField(max_length=50, null=False)
    description = models.CharField(max_length=300)
    due_datetime = models.DateTimeField()
    completion_status = models.BooleanField(default=False)
    completion_datetime = models.DateTimeField(null=True)
    files_count = models.IntegerField(default=0)
    created_datetime = models.DateTimeField(default=datetime.datetime.utcnow())
    updated_datetime = models.DateTimeField(default=datetime.datetime.utcnow())

    def save(self, *args, **kwargs):

        can_be_updated = False

        result = UserQuotaManagement.objects.get_or_create(user=self.user)
        quota_obj = result[0]

        max_allowed_tasks = UserSubscriptionLimits.objects.get(
            user_subscription_type=self.user.user_subscription_type).max_allowed_tasks

        if quota_obj.total_tasks < max_allowed_tasks:
            quota_obj.total_tasks += 1
            quota_obj.save()
            can_be_updated = True

        if can_be_updated:
            super(Task, self).save(*args, **kwargs)
        else:
            raise Exception("User Quota for Task Creation Reached.")


class TaskMediaFiles(models.Model):
    """
    NAME
        TaskMediaFiles

    DESCRIPTION

    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=50)
    file = models.FileField(null=False)
    uploaded_datetime = models.DateTimeField(default=datetime.datetime.utcnow())
    last_accessed_datetime = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)

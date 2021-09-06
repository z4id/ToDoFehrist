"""
    Contains all models for todofehrist application
"""
from enum import Enum
import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings


class UserSubscriptionTypesEnum(Enum):
    """
        Create Enums for UserSubscriptionTypes Model's attribute 'name'
    """

    FREEMIUM = 'FREEMIUM'
    PREMIUM = 'PREMIUM'


class UserSubscriptionType(models.Model):
    """
        Custom Django Model for SubscriptionType of User.
    """
    name = models.CharField(max_length=30, unique=True, null=False)
    price = models.IntegerField(default=0, null=False)
    currency = models.CharField(max_length=20, default='USD')


class UserManager(BaseUserManager):
    """
        Manager class for User
    """

    def create_app_user(self, email_address=None, password=None):
        """
        This method creates an object of User when validated data provided
        from Models' serializer.
        """
        if not email_address or not password:
            raise ValueError("Empty Signup Credentials.")

        result_ = UserSubscriptionType.objects.get_or_create(
                    name=UserSubscriptionTypesEnum.FREEMIUM.value)
        subscription_type = result_[0]

        email_address = self.normalize_email(email_address)
        user = self.model(email=email_address, username=email_address)
        user.set_password(password)
        user.subscription_type = subscription_type
        user.save()

        return user

    def create_app_user_via_oauth(self, email_address=None):
        """
        This method creates an object of User when validated data provided
        from Models' serializer.
        """
        if not email_address:
            raise ValueError("Empty Signup Credentials.")

        result_ = UserSubscriptionType.objects.get_or_create(
                    name=UserSubscriptionTypesEnum.FREEMIUM.value)
        subscription_type = result_[0]

        user = self.model(email=email_address, username=email_address)
        user.subscription_type = subscription_type
        user.is_oauth = True
        user.is_email_verified = True
        user.save()

        return user


class User(AbstractUser):
    """
        Custom Django Model for User.
    """

    is_staff = None
    is_superuser = None

    subscription_type = models.ForeignKey(UserSubscriptionType, on_delete=models.CASCADE)
    is_email_verified = models.BooleanField(default=False)
    is_oauth = models.BooleanField(default=False)
    updated_datetime = models.DateTimeField(null=True)

    class Meta:
        """
            Define Database Table Metadata
        """
        db_table = 'user'

    objects = UserManager()


class UserLogin(models.Model):
    """
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
        super(UserLogin, self).save(*args, **kwargs)

    class Meta:
        """
            Define Database Table Metadata
        """
        db_table = 'user_login'


class UserQuotaManagement(models.Model):
    """
        Custom Django Model for logging application usage for AppUser.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_tasks = models.IntegerField(default=0)
    downloaded_file_count = models.IntegerField(default=0)
    last_downloaded_datetime = models.DateTimeField(null=True)
    uploaded_files_count = models.IntegerField(default=0)
    last_uploaded_datetime = models.DateTimeField(null=True)


class UserSubscriptionLimits(models.Model):
    """
        Maintain Limitations for UserSubscriptionType
    """
    subscription_type = models.OneToOneField(UserSubscriptionType, on_delete=models.CASCADE)
    max_allowed_tasks = models.IntegerField(default=0)
    max_allowed_files = models.IntegerField(default=0)
    allowed_files_per_task = models.IntegerField(default=0)
    max_file_size = models.IntegerField(default=0)
    max_downloads_per_day = models.IntegerField(default=0)
    max_uploads_per_day = models.IntegerField(default=0)
    permanent_deletion_time = models.IntegerField(default=0)  # seconds


class Task(models.Model):
    """
        Maintain User's Task related data
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

    def delete(self, *args, **kwargs):

        result = UserQuotaManagement.objects.get_or_create(user=self.user)
        quota_obj = result[0]

        quota_obj.total_tasks -= 1
        quota_obj.save()

        super(Task, self).delete()


class TaskMediaFiles(models.Model):
    """
        Maintain Uploaded files by User for a Task
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    file = models.FileField()
    uploaded_datetime = models.DateTimeField(default=datetime.datetime.utcnow())
    last_accessed_datetime = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)

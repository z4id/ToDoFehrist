"""
    Contains all models for todofehrist application
"""
import os
from enum import Enum

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db.models import F

from todofehrist.models_utility import get_datetime_now, get_expiry_datetime


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
    name = models.CharField(max_length=30, unique=True)
    price = models.IntegerField()
    currency = models.CharField(max_length=30)


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
    updated_datetime = models.DateTimeField(default=get_datetime_now)

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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=256)
    created_at = models.DateTimeField(default=get_datetime_now)
    expire_at = models.DateTimeField(default=get_expiry_datetime)

    class Meta:
        """
            Define Database Table Metadata
        """
        db_table = 'user_login'

    def save(self, *args, **kwargs):
        """
        This method sets login/auth token's expiry datetime using created_at
        & and time margin to expire set in projects setting.py
        """
        self.created_at = get_datetime_now()
        self.expire_at = get_expiry_datetime()
        super(UserLogin, self).save(*args, **kwargs)


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
    created_datetime = models.DateTimeField(default=get_datetime_now)
    updated_datetime = models.DateTimeField(default=get_datetime_now)

    class Meta:
        ordering = ['-pk']

    def save(self, *args, **kwargs):

        max_allowed_tasks = UserSubscriptionLimits.objects.get(
            subscription_type=self.user.subscription_type).max_allowed_tasks

        # Update the total tasks count for user
        success = UserQuotaManagement.objects.filter(user=self.user, total_tasks__lt=max_allowed_tasks).update(
            total_tasks=F("total_tasks")+1)
        if success == 0:  # couldn't update or find
            query_obj, success = UserQuotaManagement.objects.get_or_create(user=self.user)
            if success:  # new object is created
                query_obj.total_tasks = 1
                query_obj.save()
            else:  # object already exists and thus has  total_tasks >= max_allowed_tasks
                raise ValueError("User Quota for Task Creation Reached.")

        super(Task, self).save(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.updated_datetime = get_datetime_now()
        super(Task, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):

        UserQuotaManagement.objects.filter(user=self.user).update(total_tasks=F('total_tasks')-1)
        super(Task, self).delete()


class TaskMediaFiles(models.Model):
    """
        Maintain Uploaded files by User for a Task
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    file = models.FileField()
    uploaded_datetime = models.DateTimeField(default=get_datetime_now)
    last_accessed_datetime = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)

    def delete(self, using=None, keep_parents=False):
        # delete file from local system
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super(TaskMediaFiles, self).delete()

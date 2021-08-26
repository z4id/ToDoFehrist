import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from todofehrist.enums import UserSubscriptionTypesEnum


class UserSubscriptionType(models.Model):
    name = models.CharField(max_length=30, unique=True, null=False)
    price = models.IntegerField(default=0, null=False)
    currency = models.CharField(max_length=20, default='USD')


class AppUser(AbstractUser):

    is_staff = None
    is_superuser = None

    user_subscription_type = models.ForeignKey(UserSubscriptionType, on_delete=models.CASCADE)
    is_email_verified = models.BooleanField(default=False)
    updated_datetime = models.DateTimeField(null=True)

    class Meta:
        db_table = 'AppUser'

    class AppUserManager(BaseUserManager):

        def create_app_user(self, email_address=None, password=None):
            if not email_address or not password:
                raise ValueError("Empty Signup Credentials.")

            result_ = UserSubscriptionType.objects.get_or_create(name=UserSubscriptionTypesEnum.Freemium.value)
            user_subscription_type = result_[0]

            email_address = self.normalize_email(email_address)
            app_user = self.model(email=email_address, username=email_address)
            app_user.set_password(password)
            app_user.user_subscription_type = user_subscription_type
            app_user.save()

            return app_user

    objects = AppUserManager()


class AppUserLogin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    token = models.CharField(max_length=256, null=False)
    created_at = models.DateTimeField(default=datetime.datetime.utcnow())
    expire_at = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        self.expire_at = self.created_at + settings.LOGIN_TOKEN_EXPIRY_TIME
        super(AppUserLogin, self).save(*args, **kwargs)

    class Meta:
        db_table = 'AppUserLogin'


class Task(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    title = models.CharField(max_length=50, null=False)
    description = models.CharField(max_length=300)
    due_datetime = models.DateTimeField()
    completion_status = models.BooleanField(default=False)
    completion_datetime = models.DateTimeField()
    files_count = models.IntegerField()
    created_datetime = models.DateTimeField()
    updated_datetime = models.DateTimeField()


class TaskMediaFiles(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=50)
    file = models.FileField()
    uploaded_datetime = models.DateTimeField()
    last_accessed_datetime = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)


class UserSubscriptionLimits(models.Model):
    user_subscription_type = models.ForeignKey(UserSubscriptionType, on_delete=models.CASCADE, null=False)
    max_allowed_tasks = models.IntegerField()
    max_allowed_files = models.IntegerField()
    allowed_files_per_task = models.IntegerField()
    max_file_size = models.IntegerField()
    max_downloads_per_day = models.IntegerField()
    max_uploads_per_day = models.IntegerField()
    permanent_deletion_time = models.IntegerField()  # seconds


class UserQuotaManagement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    total_tasks = models.IntegerField()
    downloaded_file_count = models.IntegerField()
    last_downloaded_datetime = models.DateTimeField()
    uploaded_files_count = models.IntegerField()
    last_uploaded_datetime = models.DateTimeField()
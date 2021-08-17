from django.db import models
from django.contrib.auth.models import User


class UserSubscriptionType(models.Model):
    name = models.CharField(max_length=30, unique=True, null=False)


class AppUser(User):
    user_subscription_type = models.ForeignKey(UserSubscriptionType, on_delete=models.CASCADE)
    is_email_verified = models.BooleanField(default=False)
    updated_datetime = models.DateTimeField(null=True)


class Task(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=300)
    due_datetime = models.DateTimeField()
    completion_status = models.BooleanField(default=False)
    completion_datetime = models.DateTimeField()
    files_count = models.IntegerField()
    created_datetime = models.DateTimeField()
    updated_datetime = models.DateTimeField()


class UserMediaFiles(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    file = models.FileField()
    uploaded_datetime = models.DateTimeField()
    last_accessed_datetime = models.DateTimeField()
    is_deleted = models.BooleanField()


class UserSubscriptionLimits(models.Model):
    user_subscription_type = models.ForeignKey(UserSubscriptionType, on_delete=models.CASCADE)
    max_allowed_tasks = models.IntegerField()
    max_allowed_files = models.IntegerField()
    allowed_files_per_task = models.IntegerField()
    max_file_size = models.IntegerField()
    max_downloads_per_day = models.IntegerField()
    max_uploads_per_day = models.IntegerField()
    permanent_deletion_time = models.IntegerField()  # seconds


class UserQuotaManagement(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    total_tasks = models.IntegerField()
    downloaded_file_count = models.IntegerField()
    last_downloaded_datetime = models.DateTimeField()
    uploaded_files_count = models.IntegerField()
    last_uploaded_datetime = models.DateTimeField()

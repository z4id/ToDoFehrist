from django.utils import timezone
from django.conf import settings


def get_datetime_now():
    return timezone.now()


def get_expiry_datetime():
    return timezone.now() + timezone.timedelta(seconds=settings.LOGIN_TOKEN_EXPIRY_TIME)
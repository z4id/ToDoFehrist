"""
    Contains utility methods to support todofehrist.views
"""
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.db.models.functions import ExtractWeekDay, TruncDate
from django.db.models import Count, Avg, Max

from rest_framework.response import Response
from rest_framework import status

from todofehrist.models import Task, UserLogin

from google.oauth2 import id_token
from google.auth.transport import requests

from todofehrist.models_utility import get_datetime_now


class BaseAPIView:
    """
    Create Generic Response Payload object
    """

    def __init__(self):
        pass

    def response(self, data, data_type, description, error, status_code, page_data=None):
        """
            Create Response payload with given params and return Django Response
        """
        response_data = {"success": False if error else True,
                         "payload": {},
                         "errors": error,
                         "description": description}
        response_data["payload"][data_type] = data
        if page_data:
            response_data["payload"]["total"] = page_data.get("total")
            response_data["payload"]["from"] = page_data.get("from")
            response_data["payload"]["to"] = page_data.get("to")

        return Response(response_data, status=status_code)


def send_email(subject, body, to_):
    """
    This method will send an email provided subject
    body text and list of recipients
    """

    new_email = EmailMessage(subject, body, to=to_)
    new_email.content_subtype = 'html'
    new_email.send()


def account_token_gen():
    """
    This method will return a generator class, which
    can generate and verify a token.
    """
    return PasswordResetTokenGenerator()


def send_activation_email(app_user, request):
    """
    This method will send an email to user when registered first
    time, containing an email verification link.
    args:
        - app_user
        - request
    """
    subject = 'ToDoFehrist - Activate Your Account'
    body = render_to_string('email_verification.html', {
        "domain": get_current_site(request).domain,
        "uid": urlsafe_base64_encode(force_bytes(app_user.pk)),
        "token": account_token_gen().make_token(app_user)
    })

    send_email(subject, body, [app_user.email])


def send_forgot_password_email(app_user):
    """
    This method is responsible to send forgot password email
    when a user requests it.
    """
    subject = 'ToDoFehrist - Forgot Password Request'
    body = render_to_string('forgot_password_email.html', {
        "token": account_token_gen().make_token(app_user)
    })

    send_email(subject, body, [app_user.email])


def login_required(func_handler):
    """
    This is implementation of a decorator which will be used
    by todofehrist.views to authenticate a user on each request.
    """
    def wrap(self, request, user=0, *args, **kwargs):

        user = None

        try:
            user_login = UserLogin.objects.get(token=request.META.get('HTTP_AUTHORIZATION', ''))
            if get_datetime_now() > user_login.expire_at:
                return BaseAPIView().response({}, "Invalid Token", "Resource Request",
                                              "Token Expired. Resource Access Not Allowed. Login To Continue..",
                                              status.HTTP_401_UNAUTHORIZED)
            user = user_login.user

        except UserLogin.DoesNotExist:
            return BaseAPIView().response({}, "Invalid Token", "Resource Request",
                                          "Resource Access Not Allowed. Login To Continue..",
                                          status.HTTP_401_UNAUTHORIZED)

        return func_handler(self, request, user, *args, **kwargs)

    return wrap


def gen_report_tasks_status(user):
    """
    This method generates a report for a user stating its tasks summary.
    """
    result = Task.objects.filter(user=user.id).values(
        'completion_status').annotate(total=Count('completion_status')).order_by('total')
    dict_ = {"total": 0, "complete": 0, "incomplete": 0}

    for item in result:
        if item['completion_status']:
            dict_["complete"] = item['total']
        else:
            dict_["incomplete"] = item['total']

    dict_['total'] = dict_["complete"] + dict_["incomplete"]

    response_dict = {"tasks": dict_}

    return response_dict


def gen_report_tasks_completion_avg(user):
    """
    This method returns average completion of user's tasks
    """
    result = Task.objects.filter(user=user.id, completion_status=0).values(
        date=TruncDate('completion_datetime')).annotate(avg=Count('date'))

    return result


def gen_report_incomplete_tasks_count(user):
    """
    This method will return count of incomplete/pending tasks by user.
    """
    tasks_count = Task.objects.filter(user=user.id, completion_status=0).count()

    return {"incomplete_tasks_count": tasks_count}


def gen_report_max_completion_count_day_wise(user):
    """
    This method will return daywise count of completed tasks by any user
    """
    result = Task.objects.filter(user=user.id, completion_status=1).values(
        date=TruncDate('completion_datetime')).annotate(max=Max('date'))

    return result


def gen_report_max_created_count_day_wise(user):
    """
    This method will return weekday wise data when user created more number of tasks
    than other days
    """
    result = Task.objects.filter(user=user.id).annotate(
        weekday=ExtractWeekDay('created_datetime')).values('weekday').annotate(
        tasks_count=Count('weekday'))

    day_abbr = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    dict_ = {}

    for item in result:
        day_name = day_abbr[item['weekday'] - 1]  # ExtractWeekDay method counts 1 as Sunday
        dict_[day_name] = item['tasks_count']

    return dict_


# this dictionary contains reference to method related to specific report generation
reports_config_ = {"tasks-status": gen_report_tasks_status,
                   "tasks-completion-avg": gen_report_tasks_completion_avg,
                   "incomplete-tasks-count": gen_report_incomplete_tasks_count,
                   "max-completion-count-day-wise": gen_report_max_completion_count_day_wise,
                   "max-created-count-day-wise": gen_report_max_created_count_day_wise
                   }


def reports_handler(report_name, user):
    """
    This method is responsible to return a generated report when requested by view.
    """

    report_handler = reports_config_.get(report_name, None)

    error = None
    report_data = None

    if report_handler:
        report_data = report_handler(user)
    else:
        error = 'InValidReportName'

    return report_data, error


def authenticate_oauth_token(provider, token):
    idinfo = None

    if provider != "google":
        return idinfo

    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID)
    except Exception as exception_:
        # Invalid token
        logging.exception(exception_)

    return idinfo

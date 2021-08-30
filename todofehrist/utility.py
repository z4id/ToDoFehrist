from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework.response import Response
from rest_framework import status

from todofehrist.models import Task, AppUserLogin
from django.db.models.functions import ExtractWeekDay, TruncDate
from django.db.models import Count, Avg, Max


def send_email(subject, body, to_):

    new_email = EmailMessage(subject, body, to=to_)
    new_email.send()


def account_token_gen():
    return PasswordResetTokenGenerator()


def send_activation_email(app_user, request):
    subject = 'ToDoFehrist - Activate Your Account'
    body = render_to_string('email_verification.html', {
        "domain": get_current_site(request).domain,
        "uid": urlsafe_base64_encode(force_bytes(app_user.pk)),
        "token": account_token_gen().make_token(app_user)
    })

    send_email(subject, body, [app_user.email])


def login_required(f):
    def wrap(self, request, user=0, *args, **kwargs):

        user = None

        try:
            user_login = AppUserLogin.objects.get(token=request.META.get('HTTP_AUTHORIZATION', ''))
            user = user_login.user

        except Exception as e:
            return Response({"msg": "Resource Access Not Allowed. Login To Continue..."},
                            status=status.HTTP_401_UNAUTHORIZED)

        return f(self, request, user, *args, **kwargs)

    return wrap


def gen_report_tasks_status(user):
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
    result = Task.objects.filter(user=user.id, completion_status=0).values(
        date=TruncDate('completion_datetime')).annotate(avg=Count('date'))

    return result


def gen_report_incomplete_tasks_count(user):

    tasks_count = Task.objects.filter(user=user.id, completion_status=0).count()

    return {"incomplete_tasks_count": tasks_count}


def gen_report_max_completion_count_day_wise(user):
    result = Task.objects.filter(user=user.id, completion_status=1).values(
        date=TruncDate('completion_datetime')).annotate(max=Max('date'))

    return result


def gen_report_max_created_count_day_wise(user):
    result = Task.objects.filter(user=user.id).annotate(
        weekday=ExtractWeekDay('created_datetime')).values('weekday').annotate(tasks_count=Count('weekday'))

    day_abbr = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    dict_ = dict()

    for item in result:
        day_name = day_abbr[item['weekday'] - 1]  # ExtractWeekDay method counts 1 as Sunday
        dict_[day_name] = item['tasks_count']

    return dict_


reports_config_ = {"tasks-status": gen_report_tasks_status, "tasks-completion-avg": gen_report_tasks_completion_avg,
                   "incomplete-tasks-count": gen_report_incomplete_tasks_count,
                   "max-completion-count-day-wise": gen_report_max_completion_count_day_wise,
                   "max-created-count-day-wise": gen_report_max_created_count_day_wise
                   }


def reports_handler(report_name, user):

    report_handler = reports_config_.get(report_name, None)
    error = None
    report_data = None
    if report_handler:
        report_data = report_handler(user)
    else:
        error = 'InValidReportName'

    return report_data, error

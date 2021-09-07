"""
    Contain Task to set a scheduler task for todofehrist application
    ================================================================

    Task is responsible to send emails to systems users who have pending
    tasks with due_datetime on that particular day. Task/Method will be
    invoked at 12 AM everyday (UTC Standard)
"""
from __future__ import absolute_import, unicode_literals
import os
from datetime import date

from django.db.models import Count

# Celery imports
from celery import Celery
from celery.schedules import crontab

# Project Settings import
from django.conf import settings


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emumbaproject.settings')

app = Celery('emumbaproject')
app.config_from_object('django.conf:settings')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(settings.INSTALLED_APPS)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    This method uses Celery's crontab functionality to register
    a task in queue at a specific time to be processed by active worker
    """
    # Schedule Task Every Day at 12:00 AM UTC Time
    sender.add_periodic_task(
        crontab(hour=0, minute=0),
        to_do_fehrist_tasks_reminder.s(),
    )
    # Reference add_periodic_table call method via s method
    # https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
    # Setting these up from within the on_after_configure handler means that
    # we’ll not evaluate the app at module level when using test.s()


@app.task
def to_do_fehrist_tasks_reminder():
    """
    This method will send reminder to every user
    by email who have some pending tasks in to-do
    list
    """

    from todofehrist.models import Task, User
    from todofehrist.utility import send_email

    result = Task.objects.filter(
        completion_status=0, completion_datetime__date=date.today()).values("user").annotate(
        count=Count("user"))

    for user_tasks_entry in result:
        send_email("ToDoFehrist - Pending Tasks Reminder",
                   f"You have {user_tasks_entry['count']} pending tasks due today.",
                   User.objects.get(pk=user_tasks_entry["user"]).email)

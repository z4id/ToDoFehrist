"""
NAME
    celery.py

DESCRIPTION
    Contain Task to set a scheduler task for todofehrist application
    ================================================================

    Task is responsible to send emails to systems users who have pending
    tasks with due_datetime on that particular day. Task/Method will be
    invoked at 12 AM everyday (UTC Standard)

AUTHOR: Zaid Afzal
"""
from __future__ import absolute_import, unicode_literals
import os

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
        crontab(hour=0, minute=0, day_of_month='1-31'),
        to_do_fehrist_tasks_reminder.s('Sending Tasks Reminders to All Users'),
    )


@app.task
def to_do_fehrist_tasks_reminder(arg):
    """
    This method will send reminder to every user
    by email who have some pending tasks in to-do
    list
    """

    print(arg)

    # TODO
    # Update query to send emails to users who have tasks pending for today.
    from todofehrist.models import Task
    tasks = Task.objects.filter(completion_status=1)

    for task_ in tasks:
        print(task_.due_datetime)

    print("Done")

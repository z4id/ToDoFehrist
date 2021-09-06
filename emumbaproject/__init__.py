"""
    emumbaproject contains todofehrist(a todolist Restful API) app
    =============================================================

"""
from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when
# DRF starts.
from .celery import app as celery_app

__all__ = ('celery_app', )

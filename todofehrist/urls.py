from django.urls import path
# from django.conf.urls import handler500
from django.conf import settings
from django.views.decorators.cache import cache_page

from todofehrist.views import AppUserView, activate_account, AppUserLoginView, ReportView
from todofehrist.exceptions import HTTPStatusCodeHandler

urlpatterns = [
    # User Sign Up
    path('api/user', AppUserView.as_view()),
    path('activate/<uid>/<token>', activate_account, name='activate'),

    # User Sign In
    path('api/user/login', AppUserLoginView.as_view()),

    # GET ?name= - Generate Report by Name
    path('api/v1/reports/', cache_page(settings.REPORT_CACHE_TIME)(ReportView.as_view())),
]

handler500 = HTTPStatusCodeHandler.handler500

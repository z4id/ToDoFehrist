from django.urls import path
# from django.conf.urls import handler500
from django.conf import settings
from django.views.decorators.cache import cache_page

from todofehrist.views import AppUserView, activate_account, AppUserLoginView, ReportView, AppUserResetPasswordView
from todofehrist.exceptions import HTTPStatusCodeHandler

urlpatterns = [
    # User Registration
    path('api/v1/register', AppUserView.as_view()),

    # Account Registration via Email Verification
    path('v1/activate/<uid>/<token>', activate_account, name='activate'),  # Email Verification

    # User Sign In/Log Out
    path('api/v1/auth', AppUserLoginView.as_view()),

    # User Forgot & Reset Password Request
    path('api/v1/auth/reset', AppUserResetPasswordView.as_view()),

    # User Sign In
    path('api/user/login', AppUserLoginView.as_view()),

    # GET ?name= - Generate Report by Name
    path('api/v1/reports/', cache_page(settings.REPORT_CACHE_TIME)(ReportView.as_view())),
]

handler500 = HTTPStatusCodeHandler.handler500

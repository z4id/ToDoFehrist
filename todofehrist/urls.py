from django.urls import path
# from django.conf.urls import handler500
from django.conf import settings
from django.views.decorators.cache import cache_page

from todofehrist.views import AppUserView, activate_account, AppUserLoginView, ReportView, AppUserResetPasswordView, \
    TaskView, TaskUpdateView, TaskMediaFileView
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

    # GET - Fetch All Users Tasks, POST - Create a New Task, GET ?search - Search Tasks with string
    path('api/v1/tasks', TaskView.as_view()),
    # GET - Fetch Task by ID, POST - Update Task by ID
    path('api/v1/tasks/<task_id>', TaskUpdateView.as_view()),

    # POST - Upload Task File
    path('api/v1/tasks/<task_id>/files', TaskMediaFileView.as_view()),

    # DELETE - Remove Task File, GET - Download Task File
    path('api/v1/tasks/<task_id>/files/<file_id>', TaskMediaFileView.as_view()),

    # GET ?name= - Generate Report by Name
    path('api/v1/reports/', cache_page(settings.REPORT_CACHE_TIME)(ReportView.as_view())),
]

handler500 = HTTPStatusCodeHandler.handler500

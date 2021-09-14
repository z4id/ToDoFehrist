"""
    Contain urls for ToDoFehrist app endpoints
"""
from django.urls import path, include
# from django.conf.urls import handler500
from django.conf import settings
from django.views.decorators.cache import cache_page

from todofehrist.views import UserView, activate_account, \
    UserLoginView, ReportView, UserResetPasswordView, \
    TaskView, TaskUpdateView, TaskMediaFileView, SocialAuthLogin, UserLogoutView
from todofehrist.exceptions import HTTPStatusCodeHandler

urlpatterns = [
    # User Registration
    path('register', UserView.as_view(), name='register'),

    # Account Registration via Email Verification
    path('activate/<uid>/<token>', activate_account, name='activate'),  # Email Verification

    # User Sign In
    path('auth', UserLoginView.as_view(), name='login'),

    # User Log Out
    path('auth/logout', UserLogoutView.as_view(), name='logout'),

    # User Forgot & Reset Password Request
    path('auth/reset', UserResetPasswordView.as_view()),

    path('oauth', SocialAuthLogin.as_view()),

    # GET - Fetch All Users Tasks, POST - Create a New Task, GET ?search - Search Tasks with string
    path('tasks', TaskView.as_view()),
    # GET - Fetch Task by ID, POST - Update Task by ID
    path('tasks/<task_id>', TaskUpdateView.as_view()),

    # POST - Upload Task File
    path('tasks/<task_id>/files', TaskMediaFileView.as_view()),

    # DELETE - Remove Task File, GET - Download Task File
    path('tasks/<task_id>/files/<file_id>', TaskMediaFileView.as_view()),

    # GET ?name= - Generate Report by Name
    path('reports/', cache_page(settings.REPORT_CACHE_TIME)(ReportView.as_view())),
]

# handler500 = HTTPStatusCodeHandler.handler500

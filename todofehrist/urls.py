from django.urls import path
# from django.conf.urls import handler500

from todofehrist.views import AppUserView, activate_account
from todofehrist.exceptions import HTTPStatusCodeHandler

urlpatterns = [
    # User Sign Up
    path('api/user', AppUserView.as_view()),
    path('activate/<uid>/<token>', activate_account, name='activate')
]

handler500 = HTTPStatusCodeHandler.handler500

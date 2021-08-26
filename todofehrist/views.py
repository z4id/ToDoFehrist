from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import status

import logging

from todofehrist.serializers import AppUserSerializer, AppUserLoginSerializer
from todofehrist.models import AppUser as AppUser
from todofehrist.utility import send_activation_email, account_token_gen
from django.utils.http import urlsafe_base64_decode


logger = logging.getLogger("emumbaproject.todofehrist.views.py")


class AppUserView(APIView):

    def post(self, request):

        serializer = AppUserSerializer(data=request.data)
        if not serializer.is_valid():
            logger.exception("AppUserSerializer request.data is not valid.")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        app_user = serializer.save()
        logger.info("New AppUser created and stored successfully.")

        send_activation_email(app_user, request)

        return Response({"msg": f"Sign Up Successful. An account activation link is sent to your email"
                                f"to your email '{app_user.email}'. Kindly confirm it before first login."},
                        status=status.HTTP_200_OK)


def activate_account(request, uid, token):

    try:
        uid = urlsafe_base64_decode(uid).decode()
        app_user = AppUser.objects.get(pk=uid)

        if app_user and account_token_gen().check_token(app_user, token):
            app_user.is_email_verified = True
            app_user.save()

            return HttpResponse("Great. You have verified your account. You can login now.")

    except AppUser.DoesNotExist:
        pass

    return HttpResponse("Oops. Activation Link is invalid or expired.")


class AppUserLoginView(APIView):

    def post(self, request):

        app_user = None

        try:
            app_user = AppUser.objects.get(email=request.POST.get('email', ''))

        except AppUser.DoesNotExist:
            msg = "404 - AppUserLoginView: provided email in POST request isn't valid"
            logger.exception(msg)

        if not app_user.is_email_verified:
            msg = "403 - AppUserLoginView: provided email in POST request isn't verified yet."
            logger.debug(msg)
        elif not app_user.check_password(request.POST.get('password', '')):
            msg = "403 - AppUserLoginView: provided email/password pair is not correct. Try Again."
            logger.exception(msg)

        token = account_token_gen().make_token(app_user)

        serializer_ = AppUserLoginSerializer({"user": app_user, "token": token})

        if not serializer_.is_valid():
            msg = "403 - AppUserLoginView: Login Request failed due to invalid data."
            logger.exception(msg)

        appuser_login = serializer_.save()

        msg = "200 - AppUserLoginView: UserLogged In Successfully."
        logger.info(msg)

        if appuser_login:
            return Response(serializer_.data['token'], status=status.HTTP_200_OK)







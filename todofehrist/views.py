from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import status

import logging

from todofehrist.serializers import AppUserSerializer
from todofehrist.models import AppUser as AppUser
from todofehrist.utility import send_activation_email, account_act_token_gen
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

        if app_user and account_act_token_gen().check_token(app_user, token):
            app_user.is_email_verified = True
            app_user.save()

            return HttpResponse("Great. You have verified your account. You can login now.")

    except AppUser.DoesNotExist:
        pass

    return HttpResponse("Oops. Activation Link is invalid or expired.")


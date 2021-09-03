"""
NAME
    todofehrist.views

DESCRIPTION
    This file contains all todofehrist app views.
    ============================================

AUTHOR
    Zaid Afzal
"""
import logging
from django.http import HttpResponse, FileResponse
from django.utils.http import urlsafe_base64_decode

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from todofehrist.serializers import AppUserSerializer, AppUserLoginSerializer, \
    TaskSerializer, TaskMediaFilesSerializer
from todofehrist.models import AppUser, Task, TaskMediaFiles, AppUserLogin
from todofehrist.utility import send_activation_email, account_token_gen, \
    login_required, reports_handler, send_forgot_password_email, authenticate_oauth_token

from todofehrist.serializers import SocialAuthSerializer


class AppUserView(APIView):
    """
    NAME
        AppUserView

    DESCRIPTION
        Contains handler for registering a new user.
    """

    def post(self, request):
        """
        POST request handler which validates and registers a new AppUser
        """

        serializer = AppUserSerializer(data=request.data)
        if not serializer.is_valid():
            logging.exception("AppUserSerializer request.data is not valid.")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        app_user = serializer.save()
        logging.info("New AppUser created and stored successfully.")

        send_activation_email(app_user, request)

        response_msg = f"Sign Up Successful. An account activation link is " \
                       f"sent to your email to your email '{app_user.email}', " \
                       f"Kindly confirm it before first login."

        return Response({"msg": response_msg},
                        status=status.HTTP_200_OK)


def activate_account(request, uid, token):
    """
    This is handler for verifying a user when it clicks the url
    provided in verification email.
    """

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
    """
    NAME
        AppUserLoginView

    DESCRIPTION

    """

    def post(self, request):
        """
        POST request handler
        """

        app_user = None

        try:
            app_user = AppUser.objects.get(email=request.data.get('email', ''), is_oauth=0)

        except AppUser.DoesNotExist:
            msg = "404 - AppUserLoginView: provided email in POST request isn't valid"
            logging.exception(msg)
            return Response({"msg": "Email Address doesn't exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not app_user.is_email_verified:
            msg = "403 - AppUserLoginView: provided email in POST request isn't verified yet."
            logging.debug(msg)
            return Response({"msg": "Email Address isn't verified yet."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not app_user.check_password(request.data.get('password', '')):
            msg = "403 - AppUserLoginView: provided email/password pair is not correct. Try Again."
            logging.exception(msg)
            return Response({"msg": "Email/Password pair isn't valid."},
                            status=status.HTTP_400_BAD_REQUEST)

        token = account_token_gen().make_token(app_user)

        try:
            app_user_login = AppUserLogin.objects.get(user=app_user.id)

            app_user_login.token = token
            app_user_login.save()

            return Response({"token": token},
                            status=status.HTTP_200_OK)

        except AppUserLogin.DoesNotExist:

            serializer_ = AppUserLoginSerializer(data={"user": app_user.id, "token": token})

            if not serializer_.is_valid():
                msg = "403 - AppUserLoginView: Login Request failed due to invalid data."
                logging.exception(msg)
                return Response({"msg": "Invalid Email/Password. Try Again."},
                                status=status.HTTP_400_BAD_REQUEST)

            appuser_login = serializer_.save()

            msg = "200 - AppUserLoginView: UserLogged In Successfully."
            logging.info(msg)

            return Response({"token": serializer_.data['token']},
                            status=status.HTTP_200_OK)


class AppUserLogoutView(APIView):
    """
    NAME
        AppUserLogoutView

    DESCRIPTION

    """

    @login_required
    def post(self, request, user):
        """
        Logs out a user
        """
        app_user_login = AppUserLogin.objects.get(user=user.id)
        app_user_login.delete()

        return Response({"msg": "Logged Out Successfully"}, status=status.HTTP_200_OK)


class SocialAuthLogin(APIView):
    """
    NAME
        SocialAuthLogin

    DESCRIPTION

    """

    def post(self, request):
        """
        POST request handler
        """

        social_serializer = SocialAuthSerializer(data=request.data)

        if not social_serializer.is_valid():
            return Response(social_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        social_user_info = authenticate_oauth_token(request.data["provider"], request.data["token"])

        if not social_user_info:
            return Response({"msg": "Authentication Failed."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            app_user = AppUser.objects.get(email=social_user_info["email"])

        except AppUser.DoesNotExist:

            app_user = AppUser.objects.create_app_user_via_oauth(
                email_address=social_user_info)
            app_user.save()

        token = account_token_gen().make_token(app_user)

        try:
            app_user_login = AppUserLogin.objects.get(user=app_user.id)

            app_user_login.token = token
            app_user_login.save()

            return Response({"token": token},
                            status=status.HTTP_200_OK)

        except AppUserLogin.DoesNotExist:

            serializer_ = AppUserLoginSerializer(data={"user": app_user.id, "token": token})

            if not serializer_.is_valid():
                msg = "403 - AppUserLoginView: Login Request failed due to invalid data."
                logging.exception(msg)
                return Response({"msg": "Invalid Email/Password. Try Again."},
                                status=status.HTTP_400_BAD_REQUEST)

            appuser_login = serializer_.save()

            msg = "200 - AppUserLoginView: UserLogged In Successfully."
            logging.info(msg)

            return Response({"token": serializer_.data['token']},
                            status=status.HTTP_200_OK)


class AppUserResetPasswordView(APIView):
    """
    NAME
        AppUserResetPasswordView

    DESCRIPTION

    """

    def get(self, request):
        """
        GET Request Handler
        """

        app_user = None

        try:
            app_user = AppUser.objects.get(email=request.data.get('email', ''))

        except AppUser.DoesNotExist:
            msg = "404 - AppUserLoginView: provided email in POST request isn't valid"
            logging.exception(msg)
            return Response({"msg": "Email Address doesn't exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        send_forgot_password_email(app_user)

        response_msg = f"A password reset token is sent to your email {app_user.email}"
        return Response({"msg": response_msg},
                        status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        POST request handler
        """

        app_user = None

        try:
            app_user = AppUser.objects.get(email=request.data.get('email', ''))

        except AppUser.DoesNotExist:
            msg = "404 - AppUserLoginView: provided email in POST request isn't valid"
            logging.exception(msg)
            return Response({"msg": "Email Address doesn't exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        if account_token_gen().check_token(app_user, request.data.get('reset_token', '')):
            password_ = request.data.get('new_password', None)
            if password_:
                app_user.set_password(raw_password=password_)
                app_user.save()
                return Response({"msg": "Password reset is successful."},
                                status=status.HTTP_200_OK)
            else:
                return Response({"msg": "Invalid Password String"},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"msg": "Invalid reset_token provided."},
                            status=status.HTTP_400_BAD_REQUEST)


class TaskView(APIView):
    """
    NAME
        TaskView

    DESCRIPTION

    """

    @login_required
    def get(self, request, user):
        """
        GET Request Handler
        """

        search_term = request.GET.get('search', None)

        if search_term:
            tasks = Task.objects.filter(user=user.id, title__contains=search_term)
            serializer_ = TaskSerializer(tasks, many=True)
            return Response(serializer_.data, status=status.HTTP_200_OK)

        tasks = Task.objects.filter(user=user.id)
        serializer_ = TaskSerializer(tasks, many=True)
        return Response(serializer_.data, status=status.HTTP_200_OK)

    @login_required
    def post(self, request, user):
        """
        POST Request Handler
        """
        data_ = request.data.copy()
        data_["user"] = user.id

        serializer_ = TaskSerializer(data=data_)
        if not serializer_.is_valid():
            return Response(serializer_.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = serializer_.save()
            return Response(serializer_.data, status=status.HTTP_200_OK)
        except Exception as exception_:
            return Response({"msg": "User Quota for Task Creation Reached."},
                            status=status.HTTP_400_BAD_REQUEST)


class TaskUpdateView(APIView):
    """
    NAME
        TaskUpdateView

    DESCRIPTION

    """

    @login_required
    def get(self, request, user, task_id):
        """
        GET Request Handler
        """

        task_ = None

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Exception:
            return Response({"msg": f"Task with id {task_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer_ = TaskSerializer(task_)
        return Response(serializer_.data, status=status.HTTP_200_OK)

    @login_required
    def post(self, request, user, task_id):
        """
        POST Request Handler
        """

        data_ = request.data.copy()
        data_["user"] = user.id

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Exception:
            return Response({"msg": f"Task with id {task_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer_ = TaskSerializer(data=data_, partial=True)
        if not serializer_.is_valid():
            return Response(serializer_.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer_.update(task_, data_)

        return Response(serializer_.data, status=status.HTTP_200_OK)

    @login_required
    def delete(self, request, user, task_id):
        """
        DELETE Request Handler
        """

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Exception:
            return Response({"msg": f"Task with id {task_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        task_.delete()

        return Response({"msg": f"Task with id {task_id} is deleted successfully."},
                        status=status.HTTP_200_OK)


class TaskMediaFileView(APIView):
    """
    NAME
        TaskMediaFileView

    DESCRIPTION

    """
    @login_required
    def get(self, request, user, task_id, file_id):
        """
        GET Request Handler
        """
        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Exception:
            return Response({"msg": f"Task with id {task_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            task_file = TaskMediaFiles.objects.get(id=file_id, task=task_.id)
        except Exception:
            return Response({"msg": f"File with id {file_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        file_handle = task_file.file.open()

        # send file
        response = FileResponse(file_handle, content_type='bytes')
        response['Content-Length'] = task_file.file.size
        response['Content-Disposition'] = 'attachment; filename="%s"' % task_file.file.name

        return response

    @login_required
    def post(self, request, user, task_id):
        """
        POST Request Handler
        """

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Exception:
            return Response({"msg": f"Task with id {task_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        data_ = request.data.copy()
        data_['task'] = task_id

        if data_['file']:
            data_['name'] = data_['file'].name
        else:
            data_['name'] = ''

        file_serializer = TaskMediaFilesSerializer(data=data_)

        if file_serializer.is_valid():
            file_serializer.save()
            return Response(file_serializer.data, status=status.HTTP_200_OK)

        return Response(file_serializer.errors, status=status.HTTP_200_OK)

    @login_required
    def delete(self, request, user, task_id, file_id):
        """
        DELETE Request Handler
        """
        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
            task_file = TaskMediaFiles.objects.get(id=file_id, task=task_.id)
        except Exception:
            return Response({"msg": f"File with id {file_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        task_file.delete()

        return Response({"msg": f"File with id {file_id} is deleted successfully."},
                        status=status.HTTP_200_OK)


class ReportView(APIView):
    """
    NAME
        ReportView

    DESCRIPTION

    """
    @login_required
    def get(self, request, user):
        """
        GET Request Handler
        """
        report_name = request.GET.get('name')
        report_data, error = reports_handler(report_name, user)
        if report_data:
            return Response(report_data, status=status.HTTP_200_OK)

        return Response({"msg": error}, status=status.HTTP_404_NOT_FOUND)

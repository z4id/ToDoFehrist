from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse, FileResponse
from rest_framework import status

import logging

from todofehrist.serializers import AppUserSerializer, AppUserLoginSerializer, TaskSerializer, \
    TaskMediaFilesSerializer
# from todofehrist.serializers import SocialSerializer
from todofehrist.models import AppUser as AppUser, Task, TaskMediaFiles
from todofehrist.utility import send_activation_email, account_token_gen, login_required, reports_handler, \
    send_forgot_password_email
from django.utils.http import urlsafe_base64_decode

# from rest_framework import generics, permissions
# from requests.exceptions import HTTPError
#
# from social_django.utils import load_strategy, load_backend
# from social_core.backends.oauth import BaseOAuth2
# from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden


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
            app_user = AppUser.objects.get(email=request.data.get('email', ''))

        except AppUser.DoesNotExist:
            msg = "404 - AppUserLoginView: provided email in POST request isn't valid"
            logger.exception(msg)
            return Response({"msg": "Email Address doesn't exist."}, status=status.HTTP_400_BAD_REQUEST)

        if not app_user.is_email_verified:
            msg = "403 - AppUserLoginView: provided email in POST request isn't verified yet."
            logger.debug(msg)
            return Response({"msg": "Email Address isn't verified yet."}, status=status.HTTP_400_BAD_REQUEST)

        elif not app_user.check_password(request.data.get('password', '')):
            msg = "403 - AppUserLoginView: provided email/password pair is not correct. Try Again."
            logger.exception(msg)
            return Response({"msg": "Email/Password pair isn't valid."}, status=status.HTTP_400_BAD_REQUEST)

        token = account_token_gen().make_token(app_user)

        serializer_ = AppUserLoginSerializer(data={"user": app_user.id, "token": token})

        if not serializer_.is_valid():
            msg = "403 - AppUserLoginView: Login Request failed due to invalid data."
            logger.exception(msg)
            return Response({"msg": "Invalid Email/Password. Try Again."}, status=status.HTTP_400_BAD_REQUEST)

        appuser_login = serializer_.save()

        msg = "200 - AppUserLoginView: UserLogged In Successfully."
        logger.info(msg)

        if appuser_login:
            return Response({"token": serializer_.data['token']}, status=status.HTTP_200_OK)


class AppUserResetPasswordView(APIView):

    def get(self, request):

        app_user = None

        try:
            app_user = AppUser.objects.get(email=request.data.get('email', ''))

        except AppUser.DoesNotExist:
            msg = "404 - AppUserLoginView: provided email in POST request isn't valid"
            logger.exception(msg)
            return Response({"msg": "Email Address doesn't exist."}, status=status.HTTP_400_BAD_REQUEST)

        send_forgot_password_email(app_user)

        return Response({"msg": f"A password reset token is sent to your email {app_user.email}"},
                        status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):

        app_user = None

        try:
            app_user = AppUser.objects.get(email=request.data.get('email', ''))

        except AppUser.DoesNotExist:
            msg = "404 - AppUserLoginView: provided email in POST request isn't valid"
            logger.exception(msg)
            return Response({"msg": "Email Address doesn't exist."}, status=status.HTTP_400_BAD_REQUEST)

        if account_token_gen().check_token(app_user, request.data.get('reset_token', '')):
            password_ = request.data.get('new_password', None)
            if password_:
                app_user.set_password(raw_password=password_)
                app_user.save()
                return Response({"msg": f"Password reset is successful."},
                                status=status.HTTP_200_OK)
            else:
                return Response({"msg": f"Invalid Password String"},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"msg": f"Invalid reset_token provided."},
                            status=status.HTTP_400_BAD_REQUEST)


class TaskView(APIView):

    @login_required
    def get(self, request, user):

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
        data_ = request.data.copy()
        data_["user"] = user.id

        serializer_ = TaskSerializer(data=data_)
        if not serializer_.is_valid():
            return Response(serializer_.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = serializer_.save()
            return Response(serializer_.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": "User Quota for Task Creation Reached."}, status=status.HTTP_400_BAD_REQUEST)


class TaskUpdateView(APIView):

    @login_required
    def get(self, request, user, task_id):

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

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Exception:
            return Response({"msg": f"Task with id {task_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        task_.delete()

        return Response({"msg": f"Task with id {task_id} is deleted successfully."}, status=status.HTTP_200_OK)


class TaskMediaFileView(APIView):

    @login_required
    def get(self, request, user, task_id, file_id):
        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except:
            return Response({"msg": f"Task with id {task_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            task_file = TaskMediaFiles.objects.get(id=file_id, task=task_.id)
        except:
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

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except:
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
        else:
            return Response(file_serializer.errors, status=status.HTTP_200_OK)

    @login_required
    def delete(self, request, user, task_id, file_id):
        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
            task_file = TaskMediaFiles.objects.get(id=file_id, task=task_.id)
        except Exception:
            return Response({"msg": f"File with id {file_id} doesn't exist or belong to you."},
                            status=status.HTTP_400_BAD_REQUEST)

        task_file.delete()

        return Response({"msg": f"File with id {file_id} is deleted successfully."}, status=status.HTTP_200_OK)


class ReportView(APIView):

    @login_required
    def get(self, request, user):
        report_name = request.GET.get('name')
        report_data, error = reports_handler(report_name, user)
        if report_data:
            return Response(report_data, status=status.HTTP_200_OK)
        else:
            return Response({"msg": error}, status=status.HTTP_404_NOT_FOUND)


# class SocialLoginView(generics.GenericAPIView):
#     """Auth/Login using Facebook"""
#     serializer_class = SocialSerializer
#     permission_classes = [permissions.AllowAny]
#
#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         provider = serializer.data.get('provider', None)
#         strategy = load_strategy(request)
#
#         try:
#             backend = load_backend(strategy=strategy, name=provider,
#                                    redirect_uri=None)
#
#         except MissingBackend:
#             return Response({'error': 'Please provide a valid provider'},
#                             status=status.HTTP_400_BAD_REQUEST)
#         try:
#             if isinstance(backend, BaseOAuth2):
#                 access_token = serializer.data.get('access_token')
#             user = backend.do_auth(access_token)
#         except HTTPError as error:
#             return Response({
#                 "error": {
#                     "access_token": "Invalid token",
#                     "details": str(error)
#                 }
#             }, status=status.HTTP_400_BAD_REQUEST)
#         except AuthTokenError as error:
#             return Response({
#                 "error": "Invalid credentials",
#                 "details": str(error)
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         try:
#             app_user = backend.do_auth(access_token, user=user)
#
#         except HTTPError as error:
#             return Response({
#                 "error": "invalid token",
#                 "details": str(error)
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         except AuthForbidden as error:
#             return Response({
#                 "error": "invalid token",
#                 "details": str(error)
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         if app_user:
#
#             response = {
#                 "email": app_user.email,
#                 "token": account_token_gen().make_token(app_user)
#             }
#             return Response(response, status=status.HTTP_200_OK)

"""
    This file contains all todofehrist app views.
"""
import logging
from django.http import HttpResponse, FileResponse
from django.utils.http import urlsafe_base64_decode
from django.core.paginator import Paginator, EmptyPage

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from todofehrist.serializers import UserSerializer, UserLoginSerializer, \
    TaskSerializer, TaskMediaFilesSerializer, UserRestPasswordSerializer
from todofehrist.models import User, Task, TaskMediaFiles, UserLogin
from todofehrist.utility import send_activation_email, account_token_gen, \
    login_required, reports_handler, send_forgot_password_email, authenticate_oauth_token, BaseAPIView

from todofehrist.serializers import SocialAuthSerializer


class UserView(APIView, BaseAPIView):
    """
        Contains handler for registering a new user.
    """

    def post(self, request):
        """
            User Sign Up Handler
        """

        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return self.response({}, "profile", "Sign Up", serializer.errors, status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        logging.info("New User created and stored successfully.")

        send_activation_email(user, request)

        response_msg = f"Sign Up Successful. An account activation link is " \
                       f"sent to your email to your email '{user.email}', " \
                       f"Kindly confirm it before first login."

        return self.response({}, "profile", f"{response_msg}", None, status.HTTP_200_OK)


def activate_account(request, uid, token):
    """
    This is handler for verifying a user when it clicks the url
    provided in verification email.
    """

    try:
        uid = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=uid)

        if user and account_token_gen().check_token(user, token):
            user.is_email_verified = True
            user.save()

            return HttpResponse("Great. You have verified your account. You can login now.")

    except User.DoesNotExist:
        pass

    return HttpResponse("Oops. Activation Link is invalid or expired.")


class UserLoginView(APIView, BaseAPIView):
    """
        View Handler for User Login via Email/Password
    """

    def post(self, request):
        """
            User Login Handler
        """

        user = None

        try:
            user = User.objects.get(email=request.data.get('email', ''), is_oauth=0)

        except User.DoesNotExist:
            return self.response({}, "user", "Login User", "Email Address doesn't exist.",
                                 status.HTTP_404_NOT_FOUND)

        if not user.is_email_verified:
            return self.response({}, "user", "Login User",
                                 "Email Address isn't verified yet. Check your email for verification link.",
                                 status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(request.data.get('password', '')):
            return self.response({}, "user", "Login User",
                                 "Email/Password pair isn't valid.",
                                 status.HTTP_400_BAD_REQUEST)

        token = account_token_gen().make_token(user)

        try:
            user_login = UserLogin.objects.get(user=user.id)

            user_login.token = token
            user_login.save()

            return self.response({"token": token}, "user", "User Login", None, status.HTTP_200_OK)

        except UserLogin.DoesNotExist:

            serializer_ = UserLoginSerializer(data={"user": user.id, "token": token})

            if not serializer_.is_valid():
                return self.response({}, "user", "Login User",
                                     serializer_.errors,
                                     status.HTTP_400_BAD_REQUEST)

            user_login = serializer_.save()

            return self.response({"token": token}, "user", "User Login", None, status.HTTP_200_OK)


class UserLogoutView(APIView, BaseAPIView):
    """
        View Handler to logout user upon request
    """

    @login_required
    def post(self, request, user):
        """
        Logs out a user
        """
        user_login = UserLogin.objects.get(user=user.id)
        user_login.delete()

        return self.response({}, "user", "User Logout", None, status.HTTP_200_OK)


class SocialAuthLogin(APIView, BaseAPIView):
    """
        View Handler for verifying social oauth login
        Currently supports Google OAuth Sign in
    """

    def post(self, request):
        """
            Verify provider's oauth token for login
        """

        social_serializer = SocialAuthSerializer(data=request.data)

        if not social_serializer.is_valid():
            return self.response({}, "user", "Social OAuth",
                                 social_serializer.errors,
                                 status.HTTP_400_BAD_REQUEST)

        social_user_info = authenticate_oauth_token(request.data["provider"], request.data["token"])

        if not social_user_info:
            return self.response({}, "user", "Social OAuth",
                                 "Authentication Failed.",
                                 status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=social_user_info["email"])

        except User.DoesNotExist:
            user = User.objects.create_app_user_via_oauth(
                email_address=social_user_info["email"])
            user.save()

        token = account_token_gen().make_token(user)

        try:
            user_login = UserLogin.objects.get(user=user.id)

            user_login.token = token
            user_login.save()

            return self.response({"token": token}, "user", "Social OAuth", None, status.HTTP_200_OK)

        except UserLogin.DoesNotExist:

            serializer_ = UserLoginSerializer(data={"user": user.id, "token": token})

            if not serializer_.is_valid():
                return self.response({}, "user", "Social OAuth",
                                     serializer_.errors,
                                     status.HTTP_400_BAD_REQUEST)

            user_login = serializer_.save()

            return self.response({"token": serializer_.data['token']}, "user", "Social OAuth", None, status.HTTP_200_OK)


class UserResetPasswordView(APIView, BaseAPIView):
    """
        View Handler for forgot password and reset password
    """

    def get(self, request):
        """
            Send reset password email (a token for verification)
        """

        user = None

        try:
            user = User.objects.get(email=request.data.get('email', ''))

        except User.DoesNotExist:
            return self.response({}, "user", "Forgot Password", "Email Address doesn't exist.",
                                 status.HTTP_404_NOT_FOUND)

        send_forgot_password_email(user)

        response_msg = f"A password reset token is sent to your email {user.email}"
        return self.response({}, "user", f"{response_msg}", None, status.HTTP_200_OK)

    def post(self, request):
        """
            Verify token to allow reset password option
        """

        user = None
        serializer_obj = UserRestPasswordSerializer(data=request.data.copy())

        if not serializer_obj.is_valid():
            return self.response({}, "user", "Reset Password", serializer_obj.errors,
                                 status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=request.data.get('email', ''))

        except User.DoesNotExist:
            return self.response({}, "user", "Reset Password", "Email Address doesn't exist.",
                                 status.HTTP_404_NOT_FOUND)

        if account_token_gen().check_token(user, request.data.get('reset_token', '')):
            password_ = request.data.get('new_password', None)
            if password_:
                user.set_password(raw_password=password_)
                user.save()
                return self.response({}, "user", "Reset Password", None,
                                     status.HTTP_200_OK)
            else:
                return self.response({}, "user", "Reset Password", "Invalid Password String",
                                     status.HTTP_404_NOT_FOUND)
        else:
            return self.response({}, "user", "Reset Password", "Invalid reset_token provided.",
                                 status.HTTP_404_NOT_FOUND)


class TaskView(APIView, BaseAPIView):
    """
        View Handler for Creating New Task and Getting List of Task.
        Search Task feature is also handled by this.
    """

    @login_required
    def get(self, request, user):
        """

        """

        search_term = request.GET.get('search', None)

        page_num = int(self.request.GET.get("page_num", "1"))
        page_size = int(self.request.GET.get("page_size", "5"))

        if search_term:
            tasks = Task.objects.filter(user=user.id, title__contains=search_term)

            try:
                paginator = Paginator(tasks, page_size)
                serializer_ = TaskSerializer(paginator.page(page_num), many=True, context={'request': request})

                page_data = {"total": paginator.count, "to": 1, "from": 1}
                return self.response(serializer_.data, "tasks", "Relevant Tasks", None, status.HTTP_200_OK, page_data)

            except EmptyPage:
                return self.response([], "tasks", "Relevant Tasks", "No Tasks Found.", status.HTTP_404_NOT_FOUND)

        tasks = Task.objects.filter(user=user.id)

        try:
            paginator = Paginator(tasks, page_size)
            serializer_ = TaskSerializer(paginator.page(page_num), many=True, context={'request': request})

            page_data = {"total": paginator.count, "to": 1, "from": 1}
            return self.response(serializer_.data, "tasks", "All Tasks", None, status.HTTP_200_OK, page_data)
        except EmptyPage:
            return self.response([], "tasks", "All Tasks", "No Tasks Found.", status.HTTP_404_NOT_FOUND)

    @login_required
    def post(self, request, user):
        """

        """
        data_ = request.data.copy()
        data_["user"] = user.id

        serializer_ = TaskSerializer(data=data_)
        if not serializer_.is_valid():
            return self.response({}, "task", "Create New Task", serializer_.errors, status.HTTP_400_BAD_REQUEST)

        try:
            task = serializer_.save()
            return self.response(serializer_.data, "task", "Create New Task", None, status.HTTP_200_OK)
        except Exception as exception_:
            return self.response({}, "task", "Create New Task", "User Quota for Task Creation Reached.",
                                 status.HTTP_400_BAD_REQUEST)


class TaskUpdateView(APIView, BaseAPIView):
    """
        View Handler to Fetch/Update/Delete a Task
    """

    @login_required
    def get(self, request, user, task_id):
        """

        """

        task_ = None

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Exception:
            return self.response({}, "task", "Get Task", f"Task with id {task_id} doesn't exist or belong to you.",
                                 status.HTTP_404_NOT_FOUND)

        serializer_ = TaskSerializer(task_)
        return self.response(serializer_.data, "task", "Get A Task", None, status.HTTP_200_OK)

    @login_required
    def post(self, request, user, task_id):
        """

        """

        data_ = request.data.copy()
        data_["user"] = user.id

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Task.DoesNotExist:
            return self.response({}, "task", "Update Task", f"Task with id {task_id} doesn't exist or belong to you.",
                                 status.HTTP_404_NOT_FOUND)

        serializer_ = TaskSerializer(data=data_, partial=True)
        if not serializer_.is_valid():
            return self.response({}, "task", "Update Task", serializer_.errors, status.HTTP_400_BAD_REQUEST)

        serializer_.update(task_, data_)

        return self.response(serializer_.data, "task", "Update Task", None, status.HTTP_200_OK)

    @login_required
    def delete(self, request, user, task_id):
        """
            deletes the task object.
        """

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Task.DoesNotExist:
            return self.response({}, "task", "Delete Task", f"Task with id {task_id} doesn't exist or belong to you.",
                                 status.HTTP_404_NOT_FOUND)

        task_.delete()

        return self.response({}, "task", "Delete Task", None,
                             status.HTTP_200_OK)


class TaskMediaFileView(APIView, BaseAPIView):
    """
        View handler for Uploading/Downloading/Deleting Media files for a Task
    """
    @login_required
    def get(self, request, user, task_id, file_id):
        """
            Download Task Media File
        """
        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Task.DoesNotExist:
            return self.response({}, "task", "Download File",
                                 f"Task with id {task_id} doesn't exist or belong to you.",
                                 status.HTTP_404_NOT_FOUND)

        try:
            task_file = TaskMediaFiles.objects.get(id=file_id, task=task_.id)
        except TaskMediaFiles.DoesNotExist:
            return self.response({}, "file", "Download File",
                                 f"File with id {file_id} doesn't exist or belong to you.",
                                 status.HTTP_404_NOT_FOUND)

        file_handle = task_file.file.open()

        # send file
        response = FileResponse(file_handle, content_type='bytes')
        response['Content-Length'] = task_file.file.size
        response['Content-Disposition'] = 'attachment; filename="%s"' % task_file.file.name

        return response

    @login_required
    def post(self, request, user, task_id):
        """
            Upload Task Media File
        """

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Task.DoesNotExist:
            return self.response({}, "task", "Upload File",
                                 f"Task with id {task_id} doesn't exist or belong to you.",
                                 status.HTTP_404_NOT_FOUND)

        data_ = request.data.copy()
        data_['task'] = task_id

        if data_.get('file'):
            data_['name'] = data_['file'].name

        file_serializer = TaskMediaFilesSerializer(data=data_)

        if file_serializer.is_valid():
            file_serializer.save()
            return self.response(file_serializer.data, "file", "Upload File",
                                 None,
                                 status.HTTP_200_OK)

        return self.response({}, "file", "Upload File",
                             file_serializer.errors,
                             status.HTTP_400_BAD_REQUEST)

    @login_required
    def delete(self, request, user, task_id, file_id):
        """
            Delete a Task Media File
        """
        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Task.DoesNotExist:
            return self.response({}, "task", "Delete File",
                                 f"Task with id {task_id} doesn't exist or belong to you.",
                                 status.HTTP_404_NOT_FOUND)

        try:
            task_file = TaskMediaFiles.objects.get(id=file_id, task=task_.id)
        except TaskMediaFiles.DoesNotExist:
            return self.response({}, "file", "Delete File",
                                 f"File with id {file_id} doesn't exist or belong to you.",
                                 status.HTTP_404_NOT_FOUND)

        task_file.delete()

        return self.response({}, "file", "Delete File",
                             None,
                             status.HTTP_200_OK)


class ReportView(APIView, BaseAPIView):
    """
        View Handler for Reports
    """

    @login_required
    def get(self, request, user):
        """

        """
        report_name = request.GET.get('name')
        report_data, error = reports_handler(report_name, user)
        if report_data:
            return self.response(report_data, "report", "Report Data", error, status.HTTP_200_OK)

        return self.response({}, "report", "Report Data", error, status.HTTP_404_NOT_FOUND)

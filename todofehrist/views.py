"""
    This file contains all todofehrist app views.
"""
import logging
from django.http import HttpResponse, FileResponse
from django.utils.http import urlsafe_base64_decode
from django.core.paginator import Paginator, EmptyPage

from rest_framework import status

from todofehrist.serializers import UserSerializer, UserLoginSerializer, \
    TaskSerializer, TaskMediaFilesSerializer, UserRestPasswordSerializer
from todofehrist.models import User, Task, TaskMediaFiles, UserLogin
from todofehrist.utility import send_activation_email, account_token_gen, \
    login_required, reports_handler, send_forgot_password_email, authenticate_oauth_token, BaseAPIView

from todofehrist.serializers import SocialAuthSerializer


class UserView(BaseAPIView):
    """
        Contains handler for registering a new user.
    """

    def post(self, request):
        """
            User Sign Up Handler
        """

        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return self.response_invalid(entity="profile", descripton="Sign Up", error=serializer.errors)

        user = serializer.save()
        logging.info("New User created and stored successfully.")

        send_activation_email(user, request)

        response_msg = f"Sign Up Successful. An account activation link is " \
                       f"sent to your email to your email '{user.email}', " \
                       f"Kindly confirm it before first login."

        return self.response_success(entity="profile", description=f"{response_msg}")


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


class UserLoginView(BaseAPIView):
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
            return self.response_not_found(entity="user",
                                           description="Login User", error="Email Address doesn't exist.")

        if not user.is_email_verified:
            return self.response_invalid(entity="user", description="Login User",
                                         error="Email Address isn't verified yet. Check your email for verification link.")

        if not user.check_password(request.data.get('password', '')):
            return self.response_not_found({}, entity="user", description="Login User",
                                           error="Email/Password pair isn't valid.")

        token = account_token_gen().make_token(user)

        try:
            user_login = UserLogin.objects.get(user=user.id)

            user_login.token = token
            user_login.save()

            return self.response_success(data={"token": token}, entity="user", description="User Login")

        except UserLogin.DoesNotExist:

            serializer_ = UserLoginSerializer(data={"user": user.id, "token": token})

            if not serializer_.is_valid():
                return self.response_invalid(entity="user", description="Login User", error=serializer_.errors)

            user_login = serializer_.save()

            return self.response_success({"token": token}, entity="user", description="User Login")


class UserLogoutView(BaseAPIView):
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

        return self.response_success(entity="user", description="User Logout")


class SocialAuthLogin(BaseAPIView):
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
            return self.response_invalid(entity="user", description="Social OAuth",
                                                error=social_serializer.errors)

        social_user_info = authenticate_oauth_token(request.data["provider"], request.data["token"])

        if not social_user_info:
            return self.response_invalid(entity="user", description="Social OAuth",
                                                error="Authentication Failed.")
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
            return self.response_success(data={"token": token}, entity="user", description="Social OAuth")
        except UserLogin.DoesNotExist:
            serializer_ = UserLoginSerializer(data={"user": user.id, "token": token})
            if not serializer_.is_valid():
                return self.response_invalid(entity="user", description="Social OAuth",
                                                    error=serializer_.errors)
            user_login = serializer_.save()
            return self.response_success(data={"token": serializer_.data['token']}, entity="user",
                                         description="Social OAuth")


class UserResetPasswordView(BaseAPIView):
    """
        View Handler for forgot password and reset password
    """

    def get(self, request):
        """
            Send reset password email (a token for verification)
        """

        user = None

        try:
            user = User.objects.get(email=request.data.get('email', ''), is_oauth=0)

        except User.DoesNotExist:
            return self.response_not_found(entity="user", description="Forgot Password",
                                           error="Email Address doesn't exist.")

        send_forgot_password_email(user)

        response_msg = f"A password reset token is sent to your email {user.email}"
        return self.response_success(entity="user", description=f"{response_msg}")

    def post(self, request):
        """
            Verify token to allow reset password option
        """

        user = None
        serializer_obj = UserRestPasswordSerializer(data=request.data.copy())

        if not serializer_obj.is_valid():
            return self.response_invalid(entity="user", description="Reset Password", error=serializer_obj.errors)

        try:
            user = User.objects.get(email=request.data.get('email', ''), is_oauth=0)

        except User.DoesNotExist:
            return self.response_not_found(entity="user", description="Reset Password",
                                           error="Email Address doesn't exist.")

        if account_token_gen().check_token(user, request.data.get('reset_token', '')):
            password_ = request.data.get('new_password', None)
            if password_:
                user.set_password(raw_password=password_)
                user.save()
                return self.response_success(entity="user", description="Reset Password")
            else:
                return self.response_invalid(entity="user", description="Reset Password",
                                             error="Invalid Password String")
        else:
            return self.response_not_found(entity="user", description="Reset Password",
                                           error="Invalid reset_token provided.")


class TaskView(BaseAPIView):
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
                return self.response_success(data=serializer_.data, entity="tasks",
                                             description="Relevant Tasks", page_data=page_data)

            except EmptyPage:
                return self.response_invalid(entity="tasks", description="Relevant Tasks", error="No Tasks Found.")

        tasks = Task.objects.filter(user=user.id)

        try:
            paginator = Paginator(tasks, page_size)
            serializer_ = TaskSerializer(paginator.page(page_num), many=True, context={'request': request})

            page_data = {"total": paginator.count, "to": 1, "from": 1}
            return self.response_success(data=serializer_.data, entity="tasks", description="All Tasks",
                                         page_data=page_data)
        except EmptyPage:
            return self.response_not_found(entity="tasks", description="All Tasks", error="No Tasks Found.")

    @login_required
    def post(self, request, user):
        """

        """
        data_ = request.data.copy()
        data_["user"] = user.id

        serializer_ = TaskSerializer(data=data_)
        if not serializer_.is_valid():
            return self.response_invalid("task", "Create New Task", serializer_.errors)

        try:
            task = serializer_.save()
            return self.response_success(data=serializer_.data, entity="task", description="Create New Task")
        except ValueError as exception_:
            return self.response_invalid(entity="task", description="Create New Task", error=str(exception_))


class TaskUpdateView(BaseAPIView):
    """
        View Handler to Fetch/Update/Delete a Task
    """

    @login_required
    def get(self, request, user, task_id):
        """
        """
        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Task.DoesNotExist:
            return self.response_not_found(entity="task", description="Get Task",
                                           error=f"Task with id {task_id} doesn't exist or belong to you.")

        serializer_ = TaskSerializer(task_)
        return self.response_success(data=serializer_.data, entity="task", description="Get A Task")

    @login_required
    def post(self, request, user, task_id):
        """
        """
        data_ = request.data.copy()
        data_["user"] = user.id

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Task.DoesNotExist:
            return self.response_not_found(entity="task", description="Update Task",
                                           error=f"Task with id {task_id} doesn't exist or belong to you.")

        serializer_ = TaskSerializer(data=data_, partial=True)
        if not serializer_.is_valid():
            return self.response_invalid(entity="task", description="Update Task", error=serializer_.errors)

        updated_obj = serializer_.update(task_, data_)
        serializer_ = TaskSerializer(updated_obj)

        return self.response_success(data=serializer_.data, entity="task", description="Update Task")

    @login_required
    def delete(self, request, user, task_id):
        """
            deletes the task object.
        """

        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Task.DoesNotExist:
            return self.response_not_found(entity="task", description="Delete Task",
                                           error=f"Task with id {task_id} doesn't exist or belong to you.")

        task_.delete()

        return self.response_success(entity="task", description="Delete Task")


class TaskMediaFileView(BaseAPIView):
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
            return self.response_not_found(entity="task", description="Download File",
                                           error=f"Task with id {task_id} doesn't exist or belong to you.")

        try:
            task_file = TaskMediaFiles.objects.get(id=file_id, task=task_.id)
        except TaskMediaFiles.DoesNotExist:
            return self.response_not_found(entity="file", description="Download File",
                                           error=f"File with id {file_id} doesn't exist or belong to you.")

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
            return self.response_not_found(entity="task", description="Upload File",
                                           error=f"Task with id {task_id} doesn't exist or belong to you.")

        data_ = request.data.copy()
        data_['task'] = task_id

        if data_.get('file'):
            data_['name'] = data_['file'].name

        file_serializer = TaskMediaFilesSerializer(data=data_)

        if file_serializer.is_valid():
            file_serializer.save()
            return self.response_success(data=file_serializer.data, entity="file", description="Upload File")

        return self.response_invalid(entity="file", description="Upload File", error=file_serializer.errors)

    @login_required
    def delete(self, request, user, task_id, file_id):
        """
            Delete a Task Media File
        """
        try:
            task_ = Task.objects.get(id=task_id, user=user.id)
        except Task.DoesNotExist:
            return self.response_not_found(entity="task", description="Delete File",
                                           error=f"Task with id {task_id} doesn't exist or belong to you.")

        try:
            task_file = TaskMediaFiles.objects.get(id=file_id, task=task_.id)
        except TaskMediaFiles.DoesNotExist:
            return self.response_not_found(entity="file", description="Delete File",
                                           error=f"File with id {file_id} doesn't exist or belong to you.")

        task_file.delete()

        return self.response_success(entity="file", description="Delete File")


class ReportView(BaseAPIView):
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
            return self.response_success(data=report_data, entity="report", description="Report Data")

        return self.response_not_found(entity="report", description="Report Data", error=error)

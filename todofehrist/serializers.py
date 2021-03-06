"""
    Contains Serializer classes for all Model (todofehrist.models)
"""
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from emumbaproject import settings

from todofehrist.models import User, UserLogin, Task, TaskMediaFiles
from todofehrist.models_utility import get_datetime_now


class UserSerializer(serializers.ModelSerializer):
    """
        Implements Models User's Serializer
    """
    validators_ = [UniqueValidator(queryset=User.objects.all())]
    email = serializers.EmailField(required=True, validators=validators_)

    class Meta:
        """
            Define model and attributes to use for serialization
        """
        model = User
        fields = ('id', 'email', 'password')

    def create(self, validated_data):
        """
        created an User object after validating the data received in request
        """
        user = User.objects.create_app_user(
                    email_address=validated_data['email'],
                    password=validated_data['password'])
        return user


class UserLoginSerializer(serializers.ModelSerializer):
    """
        Serializer class for UserLogin Model
    """

    token = serializers.CharField()

    class Meta:
        """
            Define model and attributes to use for serialization
        """
        model = UserLogin
        fields = ('id', 'user', 'token', 'created_at', 'expire_at')


class UserRestPasswordSerializer(serializers.Serializer):
    """
        serializer class for validating reset password request
    """
    email = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    reset_token = serializers.CharField()


class TaskSerializer(serializers.ModelSerializer):
    """
        Serializer class for Task Model
    """

    title = serializers.CharField()
    description = serializers.CharField()
    due_datetime = serializers.DateTimeField(input_formats=settings.DATETIME_FORMATS)
    files = serializers.SerializerMethodField()

    class Meta:
        """
            Define model and attributes to use for serialization
        """
        model = Task
        fields = ('id', 'user', 'title', 'description', 'due_datetime',
                  'completion_status', 'completion_datetime', 'files_count',
                  'created_datetime', 'updated_datetime', 'files')

    def update(self, instance, validated_data):
        """
        This method will update the partial data for Task object
        after validating the data received in update request.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.due_datetime = validated_data.get('due_datetime', instance.due_datetime)
        completion_status = validated_data.get('completion_status',
                                               instance.completion_status)
        if completion_status:
            instance.completion_datetime = get_datetime_now()
        else:
            instance.completion_datetime = None
        instance.completion_status = completion_status
        instance.update()
        return instance

    def get_files(self, instance):
        """
        This method serialize task related files stored in TaskMediaFiles model.
        return: list
        """
        try:
            return TaskMediaFilesSerializer(
                    TaskMediaFiles.objects.filter(task=instance.id), many=True).data
        except AttributeError:
            return []


class TaskMediaFilesSerializer(serializers.ModelSerializer):
    """
        Serializer class for TaskMediaFiles Model
    """

    file = serializers.FileField()

    class Meta:
        """
            Define model and attributes to use for serialization
        """
        model = TaskMediaFiles
        fields = ('id', 'task', 'name', 'file')


class SocialAuthSerializer(serializers.Serializer):
    """
        serializer class for validating social oauth login view
    """
    token = serializers.CharField()
    provider = serializers.CharField()

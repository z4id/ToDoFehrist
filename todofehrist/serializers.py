"""
    Contains Serializer classes for all Model (todofehrist.models)
"""
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from todofehrist.models import AppUser, AppUserLogin, Task, TaskMediaFiles


class AppUserSerializer(serializers.ModelSerializer):
    """
        Implements Models AppUser's Serializer
    """
    validators_ = [UniqueValidator(queryset=AppUser.objects.all())]
    email = serializers.EmailField(required=True, validators=validators_)

    def create(self, validated_data):
        """
        created an AppUser object after validating the data received in request
        """
        app_user = AppUser.objects.create_app_user(
                    email_address=validated_data['email'],
                    password=validated_data['password'])
        return app_user

    class Meta:
        """
            Define model and attributes to use for serialization
        """
        model = AppUser
        fields = ('id', 'email', 'password')


class AppUserLoginSerializer(serializers.ModelSerializer):
    """
        Serializer class for AppUserLogin Model
    """

    token = serializers.CharField()

    class Meta:
        """
            Define model and attributes to use for serialization
        """
        model = AppUserLogin
        fields = ('id', 'user', 'token', 'created_at', 'expire_at')


class TaskSerializer(serializers.ModelSerializer):
    """
        Serializer class for Task Model
    """

    title = serializers.CharField()
    description = serializers.CharField()
    due_datetime = serializers.DateTimeField(input_formats=['%Y-%m-%dT%H:%M:%S.%fZ'])
    completion_datetime = serializers.DateTimeField(
                            input_formats=['%Y-%m-%dT%H:%M:%S.%fZ'],
                            allow_null=True)
    files = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        """
        This method will update the partial data for Task object
        after validating the data received in update request.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.due_datetime = validated_data.get('due_datetime', instance.due_datetime)
        instance.completion_status = validated_data.get('completion_status',
                                                        instance.completion_status)
        instance.save()
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

    class Meta:
        """
            Define model and attributes to use for serialization
        """
        model = Task
        fields = ('id', 'user', 'title', 'description', 'due_datetime',
                  'completion_status', 'completion_datetime', 'files_count',
                  'created_datetime', 'updated_datetime', 'files')


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
    token = serializers.CharField(max_length=4096)
    provider = serializers.CharField()

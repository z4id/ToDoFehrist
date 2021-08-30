from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from todofehrist.models import AppUser, AppUserLogin, Task, TaskMediaFiles


class AppUserSerializer(serializers.ModelSerializer):
    validators_ = [UniqueValidator(queryset=AppUser.objects.all())]
    email = serializers.EmailField(required=True, validators=validators_)

    def create(self, validated_data):
        app_user = AppUser.objects.create_app_user(email_address=validated_data['email'], password=validated_data['password'])
        return app_user

    class Meta:
        model = AppUser
        fields = ('id', 'email', 'password')


class AppUserLoginSerializer(serializers.ModelSerializer):

    token = serializers.CharField()

    class Meta:
        model = AppUserLogin
        fields = ('id', 'user', 'token', 'created_at', 'expire_at')


class TaskSerializer(serializers.ModelSerializer):

    title = serializers.CharField()
    description = serializers.CharField()
    due_datetime = serializers.DateTimeField(input_formats=['%Y-%m-%dT%H:%M:%S.%fZ'])
    completion_datetime = serializers.DateTimeField(input_formats=['%Y-%m-%dT%H:%M:%S.%fZ'], allow_null=True)
    files = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.due_datetime = validated_data.get('due_datetime', instance.due_datetime)
        instance.completion_status = validated_data.get('completion_status', instance.completion_status)
        instance.save()
        return instance

    def get_files(self, instance):
        try:
            return TaskMediaFilesSerializer(TaskMediaFiles.objects.filter(task=instance.id), many=True).data
        except AttributeError:
            return []

    class Meta:
        model = Task
        fields = ('id', 'user', 'title', 'description', 'due_datetime', 'completion_status', 'completion_datetime',
                  'files_count', 'created_datetime', 'updated_datetime', 'files')


class TaskMediaFilesSerializer(serializers.ModelSerializer):

    file = serializers.FileField()

    class Meta:
        model = TaskMediaFiles
        fields = ('id', 'task', 'name', 'file')

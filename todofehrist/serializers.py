from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from todofehrist.models import AppUser, AppUserLogin


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
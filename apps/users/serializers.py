import datetime
import uuid

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.exceptions import ValidationError
from apps.users.models import User, Code
from django.contrib.auth.hashers import make_password
from apps.core.validators import UniqueValidator
from apps.users.services import check_email_code


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'uid', 'username', 'email', 'is_active', 'discord_id', 'is_superuser', 'level', 'points',
            'invite_code',
            'invite_user_id', "created_at")


class UserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True,
                                     validators=[UniqueValidator(queryset=User.objects.all(), message="用户名已存在")])
    password = serializers.CharField(required=True, min_length=6)
    email = serializers.EmailField(required=True,
                                   validators=[UniqueValidator(queryset=User.objects.all(), message="邮箱已存在")])
    discord_id = serializers.CharField(required=False, validators=[
        UniqueValidator(queryset=User.objects.all(), message="discord_id已存在")])
    email_code_id = serializers.IntegerField(required=True)
    email_code = serializers.CharField(required=False)

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))
        return value

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'is_active', 'discord_id', 'invite_code')

    def save(self, **kwargs):
        email_code_id = kwargs.get('email_code_id')
        email_code = kwargs.get('email_code')
        email=kwargs.get('email')
        check_email_code(email, email_code_id, email_code,delete=True)
        user = super().save(**kwargs)
        user.set_password(kwargs['password'])
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False,
                                     validators=[UniqueValidator(queryset=User.objects.all(), message="用户名已存在")])
    email = serializers.EmailField(required=False,
                                   validators=[UniqueValidator(queryset=User.objects.all(), message="邮箱已存在")])
    discord_id = serializers.CharField(required=False, validators=[
        UniqueValidator(queryset=User.objects.all(), message="discord_id已存在")])

    class Meta:
        model = User
        fields = ('username', 'email', 'discord_id', 'is_active')

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class UserPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True, min_length=6)

    class Meta:
        model = User
        fields = ('password')

    def update(self, instance, validated_data):
        instance.password = make_password(validated_data['password'])
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id", "uid", "username", "email", "is_superuser", "level", "is_active", "points", "date_joined",
            "discord_id",
            "last_login")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['date_joined'] = instance.date_joined.strftime('%Y-%m-%d %H:%M:%S')
        ret['last_login'] = instance.last_login.strftime('%Y-%m-%d %H:%M:%S')
        if instance.discord_id:
            ret['discord_id'] = instance.discord_id
        else:
            ret['discord_id'] = ""
        return ret

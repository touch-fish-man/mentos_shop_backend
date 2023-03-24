from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from apps.core.validators import CustomUniqueValidator
from apps.users.models import User, InviteCode


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'uid', 'username', 'email', 'is_active', 'discord_id', 'is_superuser', 'level', 'points',
            'invite_code',
            'invite_user_id', "created_at")


class BanUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id',)


class UserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True,
                                     validators=[
                                         CustomUniqueValidator(queryset=User.objects.all(), message="用户名已存在")])
    password = serializers.CharField(required=True, min_length=6)
    email = serializers.EmailField(required=True,
                                   validators=[
                                       CustomUniqueValidator(queryset=User.objects.all(), message="邮箱已存在")])
    discord_id = serializers.CharField(required=False, validators=[
        CustomUniqueValidator(queryset=User.objects.all(), message="discord_id已存在")])
    invite_code = serializers.CharField(required=False, validators=[
        CustomUniqueValidator(queryset=InviteCode.objects.all(), message="邀请码已存在")])

    # email_code_id = serializers.IntegerField(required=True)
    # email_code = serializers.CharField(required=False)

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))
        return value

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'is_active', 'discord_id', 'invite_code')

        extra_kwargs = {
            'email_code_id': {'required': True,"write_only": True},
            'email_code': {'required': True},
            'password': {'write_only': True},
            "uid": {"read_only": True},
        }

    def save(self, **kwargs):
        user = super().save(**kwargs)
        user.set_password(kwargs['password'])
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False,
                                     validators=[
                                         CustomUniqueValidator(queryset=User.objects.all(), message="用户名已存在")])
    email = serializers.EmailField(required=False,
                                   validators=[
                                       CustomUniqueValidator(queryset=User.objects.all(), message="邮箱已存在")])
    discord_id = serializers.CharField(required=False, validators=[
        CustomUniqueValidator(queryset=User.objects.all(), message="discord_id已存在")])

    class Meta:
        model = User
        fields = ('username', 'email', 'discord_id', 'is_active',"uid")
        extra_kwargs = {
            "uid": {"read_only": True},
        }

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
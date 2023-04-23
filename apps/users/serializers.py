from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from apps.core.validators import CustomUniqueValidator
from apps.users.models import User, InviteLog, RebateRecord
from django.core.cache import cache

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'uid', 'username', 'email', 'is_active', 'discord_id','discord_name','is_superuser', 'level', 'level_points',
            'invite_code', 'reward_points', 'invite_count', 'reward_points', 'created_at')


class BanUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id',)


class UserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True,
                                     validators=[
                                         CustomUniqueValidator(queryset=User.objects.all(), message="用户名已存在")])
    email = serializers.EmailField(required=True,
                                   validators=[
                                       CustomUniqueValidator(queryset=User.objects.all(), message="邮箱已存在")])
    discord_id = serializers.CharField(required=False,allow_blank=True)

    # email_code_id = serializers.IntegerField(required=True)
    # email_code = serializers.CharField(required=False)

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))
        value = make_password(value)
        return value
    def validate(self, attrs):
        if attrs.get("discord_id"):
            discord_id = attrs.get("discord_id", "")
            if len(discord_id) != 18:
                discord_id = None
            try:
                discord_id = int(discord_id)

                discord_name=cache.get(discord_id)
                if discord_name:
                    attrs["discord_name"]=discord_name
            except:
                discord_id = None
        return attrs
    def validate_discord_id(self, value):
        if value:
            if User.objects.filter(discord_id=value).exists():
                raise serializers.ValidationError("discord_id已存在")
        return value

    class Meta:
        model = User
        fields = ('username', 'email',"password", 'is_active', 'discord_id','id')
        extra_kwargs = {"is_active": {"read_only": True}, "id": {"read_only": True}, "discord_id": {"required": False},
                     "password": {"required": True, "min_length": 6,"write_only": True},

                        }

    def save(self, **kwargs):
        user = super().save(**kwargs)
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
        fields = ('username', 'email', 'discord_id', 'is_active', "uid", "level", "level_points", "reward_points","is_superuser")
        extra_kwargs = {
            "uid": {"read_only": True},
            "level": {"read_only": True},
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
class InviteLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteLog
        fields = '__all__'

class RebateRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RebateRecord
        fields = '__all__'


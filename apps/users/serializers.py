from rest_framework import serializers
from apps.users.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'is_active', 'discord_id', 'is_superuser', 'level', 'points', 'uid', 'last_login', 'invite_code', 'invite_user_id')
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "uid", "username", "email", "is_superuser", "level", "is_active", "points", "date_joined", "discord_id", "last_login")
    def to_representation(self, instance):
            ret = super().to_representation(instance)
            ret['date_joined'] = instance.date_joined.strftime('%Y-%m-%d %H:%M:%S')
            ret['last_login'] = instance.last_login.strftime('%Y-%m-%d %H:%M:%S')
            if instance.discord_id:
                ret['discord_id'] = instance.discord_id
            else:
                ret['discord_id'] = ""
            return ret
from rest_framework import serializers
from apps.users.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'is_active', 'discord_id', 'is_superuser', 'level', 'points', 'uid', 'last_login', 'invite_code', 'invite_user_id')

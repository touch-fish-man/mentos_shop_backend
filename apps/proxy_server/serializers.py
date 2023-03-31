from rest_framework import serializers

from apps.core.serializers import CommonSerializer
from apps.proxy_server.models import Acls, Server, ProxyList
from apps.core.validators import CustomUniqueValidator


class AclsSerializer(CommonSerializer):
    class Meta:
        model = Acls
        fields = '__all__'


class AclsCreateSerializer(CommonSerializer):
    class Meta:
        model = Acls
        fields = '__all__'

    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(Acls.objects.all(), message="acl名称已存在")])
    acl_value = serializers.CharField(required=True)


class AclsUpdateSerializer(CommonSerializer):
    class Meta:
        model = Acls
        fields = '__all__'

    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(Acls.objects.all(), message="acl名称已存在")])
    acl_value = serializers.CharField(required=True)
    read_only_fields = ('id', 'created_at', 'updated_at')


class ServerSerializer(CommonSerializer):

    class Meta:
        model = Server
        fields = '__all__'


class ServerCreateSerializer(CommonSerializer):
    class Meta:
        model = Server
        fields = '__all__'

    name = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器名称已存在")])
    ip = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器ip已存在")])
    port = serializers.IntegerField(required=True)


class ServerUpdateSerializer(CommonSerializer):
    class Meta:
        model = Server
        fields = '__all__'

    name = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器名称已存在")])
    ip = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器ip已存在")])
    port = serializers.IntegerField(required=True)
    read_only_fields = ('id', 'created_at', 'updated_at')

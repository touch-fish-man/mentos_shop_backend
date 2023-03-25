from rest_framework import serializers

from apps.core.serializers import CommonSerializer
from apps.proxy_server.models import AclList, ProxyServer, ProxyList
from apps.core.validators import CustomUniqueValidator


class AclListSerializer(CommonSerializer):
    class Meta:
        model = AclList
        fields = '__all__'


class AclListCreateSerializer(CommonSerializer):
    class Meta:
        model = AclList
        fields = '__all__'

    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(AclList.objects.all(), message="acl名称已存在")])
    acl_value = serializers.CharField(required=True)


class AclListUpdateSerializer(CommonSerializer):
    class Meta:
        model = AclList
        fields = '__all__'

    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(AclList.objects.all(), message="acl名称已存在")])
    acl_value = serializers.CharField(required=True)
    read_only_fields = ('id', 'created_at', 'updated_at')


class ProxyServerSerializer(CommonSerializer):
    class Meta:
        model = ProxyServer
        fields = '__all__'


class ProxyServerCreateSerializer(CommonSerializer):
    class Meta:
        model = ProxyServer
        fields = '__all__'

    name = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(ProxyServer.objects.all(), message="代理服务器名称已存在")])
    ip = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(ProxyServer.objects.all(), message="代理服务器ip已存在")])
    port = serializers.IntegerField(required=True)


class ProxyServerUpdateSerializer(CommonSerializer):
    class Meta:
        model = ProxyServer
        fields = '__all__'

    name = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(ProxyServer.objects.all(), message="代理服务器名称已存在")])
    ip = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(ProxyServer.objects.all(), message="代理服务器ip已存在")])
    port = serializers.IntegerField(required=True)
    read_only_fields = ('id', 'created_at', 'updated_at')

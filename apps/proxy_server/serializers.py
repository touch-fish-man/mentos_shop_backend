from rest_framework import serializers

from apps.core.serializers import CommonSerializer
from apps.proxy_server.models import Acls, Server, ProxyList,ServerGroup
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

class ServerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerGroup
        fields = ('id', 'name')

class ServerSerializer(CommonSerializer):
    server_groups=ServerGroupSerializer(many=True)

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


class ServerUpdateSerializer(CommonSerializer):
    server_groups = serializers.PrimaryKeyRelatedField(queryset=ServerGroup.objects.all(), many=True)
    class Meta:
        model = Server
        fields = ('id', 'name', 'ip', 'description','cidr_prefix','server_groups')

    name = serializers.CharField(required=False, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器名称已存在")])
    ip = serializers.CharField(required=False, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器ip已存在")])
    extra_kwargs = {
        'id': {'read_only': True},
        'created_at': {'read_only': True},
        'updated_at': {'read_only': True}}
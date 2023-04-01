from rest_framework import serializers

from apps.core.serializers import CommonSerializer
from apps.proxy_server.models import Acls, Server, Proxy, ServerGroup, AclGroup
from apps.core.validators import CustomUniqueValidator


class AclsSerializer(CommonSerializer):
    class Meta:
        model = Acls
        fields = '__all__'


class AclsGroupSerializer(CommonSerializer):
    class Meta:
        model = Acls
        fields = ('id', 'name')


class AclGroupSerializer(CommonSerializer):
    acls = AclsGroupSerializer(many=True)

    class Meta:
        model = AclGroup
        fields = '__all__'


class AclGroupCreateSerializer(CommonSerializer):
    acls = serializers.PrimaryKeyRelatedField(many=True, queryset=Acls.objects.all(), required=False)
    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(AclGroup.objects.all(), message="acl组名称已存在")])
    description = serializers.CharField(required=True)

    class Meta:
        model = AclGroup
        fields = ('id', 'name', 'description', 'acls')


class AclsCreateSerializer(CommonSerializer):
    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(Acls.objects.all(), message="acl名称已存在")])
    acl_value = serializers.CharField(required=True)

    class Meta:
        model = Acls
        fields = ('name', 'description', 'acl_value')


class AclsUpdateSerializer(CommonSerializer):
    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(Acls.objects.all(), message="acl名称已存在")])
    acl_value = serializers.CharField(required=True)

    class Meta:
        model = Acls
        fields = ('name', 'description', 'acl_value')


class ServerSerializer(CommonSerializer):
    class Meta:
        model = Server
        fields = '__all__'


class ServersGroupSerializer(CommonSerializer):
    class Meta:
        model = Server
        fields = ('id', 'name')


class ServerGroupSerializer(serializers.ModelSerializer):
    servers = serializers.PrimaryKeyRelatedField(many=True, queryset=Server.objects.all(), required=False)

    class Meta:
        model = ServerGroup
        fields = ('id', 'name', 'description', 'servers')


class ServerGroupUpdateSerializer(CommonSerializer):
    class Meta:
        model = ServerGroup
        fields = ('id', 'name', 'description', 'servers')

    name = serializers.CharField(required=False,
                                 validators=[CustomUniqueValidator(ServerGroup.objects.all(),
                                                                   message="代理服务器组名称已存在")])
    description = serializers.CharField(required=False)


class ServerCreateSerializer(CommonSerializer):
    class Meta:
        model = Server
        fields = '__all__'

    name = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器名称已存在")])
    ip = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器ip已存在")])


class ServerUpdateSerializer(CommonSerializer):
    class Meta:
        model = Server
        fields = ('id', 'name', 'ip', 'description', 'cidr_prefix')

    name = serializers.CharField(required=False, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器名称已存在")])
    ip = serializers.CharField(required=False, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器ip已存在")])
    extra_kwargs = {
        'id': {'read_only': True},
        'created_at': {'read_only': True},
        'updated_at': {'read_only': True}}

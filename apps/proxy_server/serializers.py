from rest_framework import serializers

from apps.core.serializers import CommonSerializer
from apps.proxy_server.models import Acls, Server, Proxy, ServerGroup, AclGroup, Cidr,cidr_ip_count
from apps.core.validators import CustomUniqueValidator


class AclsSerializer(CommonSerializer):
    class Meta:
        model = Acls
        fields = '__all__'


class AclsGroupSerializer(CommonSerializer):
    class Meta:
        model = Acls
        fields = ('id', 'name')

class CidrSerializer(CommonSerializer):
    class Meta:
        model = Cidr
        fields = ('id', 'cidr', 'ip_count')
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

    def create(self, validated_data):
        acl_value = []
        for acl in validated_data['acls']:
            acl_value.extend(acl.acl_value.split('\n'))
        acl_value = list(set(acl_value))
        acl_value.sort()
        validated_data['acl_value'] = "\n".join(acl_value)
        # 判断是否有重复的acl_value
        if AclGroup.objects.filter(acl_value=validated_data['acl_value']).exists():
            raise serializers.ValidationError("acl组已存在")
        return super().create(validated_data)

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
    cidrs = CidrSerializer(many=True)
    class Meta:
        model = Server
        fields = ('id', 'name', 'ip', 'description', 'cidrs')


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

class CidrCreateSerializer(CommonSerializer):
    class Meta:
        model = Cidr
        fields = ('cidr','ip_count')
        extra_kwargs = {
        'ip_count': {'read_only': True}}

class ServerCreateSerializer(CommonSerializer):
    cidrs = CidrCreateSerializer(many=True)
    class Meta:
        model = Server
        fields = '__all__'

    name = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器名称已存在")])
    def create(self, validated_data):
        cidrs = validated_data.pop('cidrs')
        server = Server.objects.create(**validated_data)
        cidrs_list = []
        for cidr in cidrs:
            cidr['ip_count'] = cidr_ip_count(cidr['cidr'])
            cidr_obj= Cidr.objects.get_or_create(**cidr)
            cidrs_list.append(cidr_obj[0].id)
        server.cidrs.set(cidrs_list)
        return server


class ServerUpdateSerializer(CommonSerializer):
    cidrs = CidrCreateSerializer(many=True)
    class Meta:
        model = Server
        fields = ('id', 'name', 'ip', 'description', 'cidrs')

    name = serializers.CharField(required=False, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器名称已存在")])
    extra_kwargs = {
        'id': {'read_only': True},
        'created_at': {'read_only': True},
        'updated_at': {'read_only': True}}
    def update(self, instance, validated_data):
        cidrs = validated_data.pop('cidrs')
        instance.cidrs.clear()
        for cidr in cidrs:
            cidr['ip_count'] = cidr_ip_count(cidr['cidr'])
            cidr_obj= Cidr.objects.get_or_create(**cidr)
            instance.cidrs.add(cidr_obj[0].id)
        instance = super().update(instance, validated_data)
        return instance

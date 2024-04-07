import ipaddress

from django.core.exceptions import ValidationError
from rest_framework import serializers

from apps.core.serializers import CommonSerializer
from apps.proxy_server.models import Acls, Server, Proxy, ServerGroup, AclGroup, Cidr, cidr_ip_count, fix_network_by_ip
from apps.core.validators import CustomUniqueValidator, CustomValidationError
from apps.proxy_server.services import update_product_acl
from apps.utils.kaxy_handler import KaxyClient
from django.core.validators import validate_ipv46_address
import logging


class AclsSerializer(CommonSerializer):
    class Meta:
        model = Acls
        fields = '__all__'
        extra_kwargs = {
            "id": {'read_only': True},
            "created_at": {'read_only': True},
            "updated_at": {'read_only': True}
        }


class AclsCidrSerializer(CommonSerializer):
    class Meta:
        model = Acls
        fields = ('id', 'name')


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
            raise ValidationError("已存在内容相同的acl组")
        return super().create(validated_data)

    class Meta:
        model = AclGroup
        fields = ('id', 'name', 'description', 'acls')


class AclGroupUpdateSerializer(CommonSerializer):
    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(AclGroup.objects.all(), message="acl组名称已存在")])
    description = serializers.CharField(required=True)
    acls = serializers.PrimaryKeyRelatedField(many=True, queryset=Acls.objects.all(), required=False)

    def update(self, instance, validated_data):
        validated_data['acl_value'] = AclGroup.get_acl_values(validated_data.get('acls'))
        return super().update(instance, validated_data)

    class Meta:
        model = AclGroup
        fields = ('id', 'name', 'description', 'acls')


class AclsCreateSerializer(CommonSerializer):
    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(Acls.objects.all(), message="acl名称已存在")])
    acl_value = serializers.CharField(required=True)
    shopify_variant_id = serializers.CharField(required=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

    class Meta:
        model = Acls
        fields = ('name', 'description', 'acl_value', 'shopify_variant_id', 'price')


class AclsUpdateSerializer(CommonSerializer):
    name = serializers.CharField(required=True,
                                 validators=[CustomUniqueValidator(Acls.objects.all(), message="acl名称已存在")])
    acl_value = serializers.CharField(required=True)
    shopify_variant_id = serializers.CharField(required=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

    class Meta:
        model = Acls
        fields = ('name', 'description', 'acl_value', 'shopify_variant_id', 'price')


class ServerSerializer(CommonSerializer):
    cidrs = CidrSerializer(many=True)

    class Meta:
        model = Server
        fields = ('id', 'name', 'ip', 'description', 'cidrs', 'server_status')


class ServersGroupSerializer(CommonSerializer):
    class Meta:
        model = Server
        fields = ('id', 'name')


class ServerGroupSerializer(CommonSerializer):
    servers = ServersGroupSerializer(many=True)

    class Meta:
        model = ServerGroup
        fields = ('id', 'name', 'description', 'servers')


class ServerGroupCreateSerializer(serializers.ModelSerializer):
    servers = serializers.PrimaryKeyRelatedField(many=True, queryset=Server.objects.all(), required=False)

    class Meta:
        model = ServerGroup
        fields = ('id', 'name', 'description', 'servers')


class ServerGroupUpdateSerializer(CommonSerializer):
    class Meta:
        model = ServerGroup
        fields = ('id', 'name', 'description', 'servers')

    servers = serializers.PrimaryKeyRelatedField(many=True, queryset=Server.objects.all(), required=False)

    name = serializers.CharField(required=False,
                                 validators=[CustomUniqueValidator(ServerGroup.objects.all(),
                                                                   message="代理服务器组名称已存在")])
    description = serializers.CharField(required=False)


class CidrCreateSerializer(CommonSerializer):
    class Meta:
        model = Cidr
        fields = ('cidr', 'ip_count')
        extra_kwargs = {
            'ip_count': {'read_only': True}}


class ServerCreateSerializer(CommonSerializer):
    cidrs = CidrCreateSerializer(many=True)
    run_init = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    port = serializers.CharField(required=False)
    update_cidr = serializers.CharField(required=False)

    class Meta:
        model = Server
        fields = '__all__'

    name = serializers.CharField(required=True, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器名称已存在")])

    def validate(self, attrs):
        try:
            validate_ipv46_address(attrs['ip'])
        except Exception:
            return CustomValidationError("ip地址格式错误")
        cidrs = attrs['cidrs']
        for cidr in cidrs:
            try:
                update_i = ipaddress.ip_network(cidr['cidr'])
            except Exception:
                raise CustomValidationError("cidr格式错误")
        if "run_init" in attrs:
            run_init=attrs.pop("run_init")
        if "password" in attrs:
            password=attrs.pop("password")
        if "port" in attrs:
            port=attrs.pop("port")
        if "update_cidr" in attrs:
            update_cidr=attrs.pop("update_cidr")
            from apps.proxy_server.tasks import init_server
            init_server.delay(attrs['ip'], port, "root", password, attrs['cidrs'], run_init, update_cidr)

        return attrs

    def create(self, validated_data):
        cidrs = validated_data.pop('cidrs')
        server = Server.objects.create(**validated_data)
        cidrs_list = []
        for cidr in cidrs:
            cidr['cidr'] = fix_network_by_ip(cidr['cidr'].strip())
            cidr['ip_count'] = cidr_ip_count(cidr['cidr'])
            cidr_obj = Cidr.objects.get_or_create(**cidr)
            cidrs_list.append(cidr_obj[0].id)
        server.cidrs.set(cidrs_list)
        return server


class ServerUpdateSerializer(CommonSerializer):
    cidrs = CidrCreateSerializer(many=True)
    run_init = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    port = serializers.CharField(required=False)
    update_cidr = serializers.CharField(required=False)

    class Meta:
        model = Server
        fields = ('id', 'name', 'ip', 'description', 'cidrs')

    name = serializers.CharField(required=False, validators=[
        CustomUniqueValidator(Server.objects.all(), message="代理服务器名称已存在")])
    extra_kwargs = {
        'id': {'read_only': True},
        'created_at': {'read_only': True},
        'updated_at': {'read_only': True}}

    def validate(self, attrs):
        run_init, update_cidr = False , False
        if "run_init" in attrs:
            run_init=attrs.pop("run_init")=="1"
        if "password" in attrs:
            password=attrs.pop("password")=="1"
        if "port" in attrs:
            port=attrs.pop("port")
        if "update_cidr" in attrs:
            update_cidr=attrs.pop("update_cidr")
        if run_init or update_cidr:
            from apps.proxy_server.tasks import init_server
            init_server.delay(attrs['ip'], port, "root", password, attrs['cidrs'], run_init, update_cidr)
        # # 检查cidr是否在代理服务器的cidr范围内
        # cidrs = attrs['cidrs']
        # try:
        #     c_client = KaxyClient(attrs['ip'], clean_fail_cnt=True)
        #     if not c_client.status:
        #         raise CustomValidationError("代理服务器连接失败，请检查服务器是否正常")
        #     server_cidrs = c_client.get_cidr()
        # except Exception as e:
        #     raise CustomValidationError("代理服务器连接失败，请检查服务器是否正常")
        # check_cidr_cnt = 0
        # for cidr in cidrs:
        #     for s_cidr in server_cidrs:
        #         update_i = ipaddress.ip_network(cidr['cidr'])
        #         server_i = ipaddress.ip_network(s_cidr)
        #         if update_i.subnet_of(server_i):
        #             check_cidr_cnt += 1
        #             break
        # if check_cidr_cnt != len(cidrs):
        #     raise CustomValidationError("配置的cidr不在代理服务器的cidr范围内，请重新配置")
        return attrs

    def update(self, instance, validated_data):
        cidrs = validated_data.pop('cidrs')
        instance.fail_count = 0
        instance.server_status = 1  # 重置状态

        instance.cidrs.clear()
        for cidr in cidrs:
            cidr['ip_count'] = cidr_ip_count(cidr['cidr'])
            cidr_obj, if_create = Cidr.objects.get_or_create(**cidr)
            instance.cidrs.add(cidr_obj.id)
        instance = super().update(instance, validated_data)
        # from apps.products.tasks import update_product_stock
        # result = update_product_stock.delay()
        # if result.ready():
        #     if result.failed():
        #         result = result.result
        #         error_msg = result.result.get("exc_message", [])[-1]
        #         logging.error("Task failed with exception:{}".format(result.result))
        #         logging.error("Traceback:{}".format(result.traceback))
        #         raise CustomValidationError("更新商品库存失败,请修改后重试:{}".format(error_msg))
        return instance


class CidrSerializer(CommonSerializer):
    exclude_acl = AclsCidrSerializer(many=True)

    class Meta:
        model = Cidr
        fields = ('id', 'cidr', 'ip_count', 'exclude_acl')
        extra_kwargs = {
            'ip_count': {'read_only': True},
            "cidr": {'read_only': True},
            'id': {'read_only': True}
        }


class CidrUpdateSerializer(CommonSerializer):
    exclude_acl = serializers.PrimaryKeyRelatedField(many=True, queryset=Acls.objects.all(), required=False)

    class Meta:
        model = Cidr
        fields = ('id', 'exclude_acl')
        extra_kwargs = {
            'id': {'read_only': True}
        }

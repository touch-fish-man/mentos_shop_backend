import logging
from pprint import pprint

from apps.core.validators import CustomValidationError
from rest_framework import serializers
from .models import Product, Variant, ProductTag, ProductCollection, Option, OptionValue
from apps.proxy_server.models import Acls, Cidr, ProxyStock
from apps.proxy_server.serializers import ServersGroupSerializer,AclsGroupSerializer,AclGroup,ServerGroup
from apps.proxy_server.models import ServerGroupThrough,ServerCidrThrough
from drf_writable_nested.serializers import WritableNestedModelSerializer


class OptionValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionValue
        fields = ('option_value',)




class OptionSerializer(serializers.ModelSerializer):
    option_values = OptionValueSerializer(many=True)

    class Meta:
        model = Option
        fields = ('option_name', 'option_type', 'shopify_option_id', 'option_values')

    def create(self, validated_data):
        # 先创建option,再创建option_value,add
        option_values_data = validated_data.pop('option_values')
        option = Option.objects.create(**validated_data)
        for option_value_data in option_values_data:
            option_value_data['option'] = option
            option_value_data['product'] = option.product
            if OptionValue.objects.filter(option_value=option_value_data.get('option_value'), option=option).exists():
                OptionValue.objects.get(option_value=option_value_data.get('option_value'), option=option)
            else:
                OptionValue.objects.create(**option_value_data)
        return option


class VariantSerializer(serializers.ModelSerializer):
    server_group = ServersGroupSerializer()
    acl_group = AclsGroupSerializer()
    class Meta:
        model = Variant
        fields = ("id",
            "shopify_variant_id", 'variant_name', 'variant_desc', 'server_group', 'acl_group', 'cart_step', 'is_active',
            'variant_price',
            'variant_stock', 'variant_option1', 'variant_option2', 'variant_option3',"proxy_time")
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if not ret["variant_desc"]:
            ret["variant_desc"] = ''
        return ret

class VariantCreateSerializer(serializers.ModelSerializer):
    cart_step = serializers.IntegerField(required=True)
    variant_price = serializers.FloatField(required=True)
    server_group = serializers.PrimaryKeyRelatedField(queryset=ServerGroup.objects.all(), required=True)
    acl_group = serializers.PrimaryKeyRelatedField(queryset=AclGroup.objects.all(), required=True)
    class Meta:
        model = Variant
        fields = (
            "shopify_variant_id", 'variant_name', 'variant_desc', 'server_group', 'acl_group', 'cart_step', 'is_active',
            'variant_price',
            'variant_stock', 'variant_option1', 'variant_option2', 'variant_option3',"proxy_time")
    def get_cidr(self,server_group):
        cidr_ids = []
        if server_group:

            server_ids=ServerGroupThrough.objects.filter(server_group_id=server_group.id).values_list('server_id', flat=True)
            cidr_ids=ServerCidrThrough.objects.filter(server_id__in=server_ids).values_list('cidr_id', flat=True)
            ip_count = Cidr.objects.filter(id__in=cidr_ids).values_list('ip_count', flat=True)
            return cidr_ids,ip_count
        else:
            return cidr_ids,[]

    def create(self, validated_data):
        variant = Variant.objects.create(**validated_data)
        cidr_ids,ip_count=self.get_cidr(validated_data.get('server_group'))
        acl_group_id = validated_data.get('acl_group').id
        for idx, cidr_id in enumerate(cidr_ids):
            cart_stock = ip_count[idx]//validated_data.get('cart_step')
            if ProxyStock.objects.filter(cidr_id=cidr_id, acl_group_id=acl_group_id,cart_stock=cart_stock).exists():
                # 如果已经存在，就不创建了
                continue
            porxy_stock = ProxyStock.objects.get_or_create(cidr_id=cidr_id, acl_group_id=acl_group_id, ip_stock=ip_count[idx],cart_step=validated_data.get('cart_step'),cart_stock=cart_stock)
            subnets = porxy_stock.gen_subnets()
            porxy_stock.subnets = ",".join(subnets)
            porxy_stock.available_subnets = porxy_stock.subnets
            porxy_stock.save()
        variant.save()
        return variant

class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = ('id','tag_name', 'tag_desc')
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def create(self, validated_data):
        product_tag, _ = ProductTag.objects.get_or_create(**validated_data)
        return product_tag
class VariantUpdateSerializer(serializers.ModelSerializer):
    cart_step = serializers.IntegerField(required=True)
    variant_price = serializers.FloatField(required=True)
    server_group = serializers.PrimaryKeyRelatedField(queryset=ServerGroup.objects.all(), required=True)
    acl_group = serializers.PrimaryKeyRelatedField(queryset=AclGroup.objects.all(), required=True)
    shopify_variant_id = serializers.CharField(required=False)
    id = serializers.CharField(required=False)
    class Meta:
        model = Variant
        fields = ('id','variant_name', 'variant_desc', 'server_group', 'acl_group', 'cart_step', 'is_active',
            'variant_price','shopify_variant_id',
            'variant_stock', 'variant_option1', 'variant_option2', 'variant_option3',"proxy_time")
        extra_kwargs = {
            'shopify_variant_id': {'read_only': True},
            'id': {'read_only': True},
        }
    def get_cidr(self,server_group):
        cidr_ids = []
        if server_group:
            server_group_id=server_group.id

            server_ids=ServerGroupThrough.objects.filter(server_group_id=server_group_id).values_list('server_id', flat=True)
            cidr_ids=ServerCidrThrough.objects.filter(server_id__in=server_ids).values_list('cidr_id', flat=True)
            ip_count = Cidr.objects.filter(id__in=cidr_ids).values_list('ip_count', flat=True)
            return cidr_ids,ip_count
        else:
            return cidr_ids,[]
    def validate(self, attrs):
        logging.info(attrs)
        logging.info(self.instance)
        # cidr_ids,ip_count=self.get_cidr(attrs.get('server_group'))
        # acl_group_id = attrs.get('acl_group').id
        # for idx, cidr_id in enumerate(cidr_ids):
        #     # 如果cidr_id不存在，则创建,否则更新cart_step
        #     if not ProxyStock.objects.filter(variant_id=attrs.get(id), acl_group_id=acl_group_id,cidr_id=cidr_id).first():
        #         cart_stock = ip_count[idx]//attrs.get('cart_step')
        #         porxy_stock = ProxyStock.objects.create(cidr_id=cidr_id, acl_group_id=acl_group_id, ip_stock=ip_count[idx], variant_id=self.id,cart_step=attrs.get('cart_step'),cart_stock=cart_stock)
        #         subnets = porxy_stock.gen_subnets()
        #         porxy_stock.subnets = ",".join(subnets)
        #         porxy_stock.available_subnets = porxy_stock.subnets
        #         porxy_stock.save()
        #     else:
        #         porxy_stock = ProxyStock.objects.filter(variant_id=instance.id, acl_group_id=instance.acl_group_id,cidr_id=cidr_id).first()
        #         porxy_stock.cart_step = validated_data.get('cart_step')
        #         # TODO 需要重新计算cidr
        #         porxy_stock.cart_stock = ip_count[idx]//validated_data.get('cart_step')
        #         porxy_stock.save()
        return attrs

    def save(self, **kwargs):
        return super().save(**kwargs)


class ProductCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCollection
        fields = ('id', 'collection_name', 'collection_desc', 'shopify_collection_id')

    def create(self, validated_data):
        product_collection,_=ProductCollection.objects.get_or_create(**validated_data)
        return product_collection


class ProductSerializer(serializers.ModelSerializer):
    product_collections = ProductCollectionSerializer(many=True)
    product_tags = ProductTagSerializer(many=True)
    variants = VariantSerializer(many=True)
    variant_options = OptionSerializer(many=True)
    lower_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id",
                  'product_name', 'product_desc', 'shopify_product_id', 'product_tags', 'product_collections',
                  'variants',
                  'variant_options',"created_at","lower_price")
    def get_lower_price(self, obj):
        if obj.variants.exists():
            return "$"+str(obj.variants.order_by('variant_price').first().variant_price)+"+"
        else:
            return "$0.0+"


class ProductCreateSerializer(serializers.ModelSerializer):
    product_collections = ProductCollectionSerializer(many=True, required=True)
    product_tags = ProductTagSerializer(many=True, required=True)
    variants = VariantCreateSerializer(many=True, required=True)
    variant_options = OptionSerializer(many=True, required=True)

    class Meta:
        model = Product
        fields = (
            'product_name', 'product_desc', 'shopify_product_id', 'product_tags', 'product_collections',
            'variants',
            'variant_options')
    def validate_product_collections(self, product_collections):
        if not product_collections:
            raise CustomValidationError("产品系列不能为空,请在shopify中添加后重新同步")
        return product_collections

    def create(self, validated_data):
        # 先创建variant,再创建product,再add
        variants_data = validated_data.pop('variants')
        product_collections_data = validated_data.pop('product_collections')
        product_tags_data = validated_data.pop('product_tags')
        options_data = validated_data.pop('variant_options')
        product = Product.objects.create(**validated_data)
        # 创建option
        for option_data in options_data:
            option_data['product'] = product
            OptionSerializer().create(option_data)  # 创建variant
        for variant_data in variants_data:
            variant_data['product'] = product
            VariantCreateSerializer().create(variant_data)
        # 创建product_collection
        for product_collection_data in product_collections_data:
            product_collection = ProductCollectionSerializer().create(product_collection_data)
            product.product_collections.add(product_collection)
        # 创建product_tag
        for product_tag_data in product_tags_data:
            product_tag = ProductTagSerializer().create(product_tag_data)
            product.product_tags.add(product_tag)
        return product
class ProductUpdateSerializer(WritableNestedModelSerializer):
    product_collections = ProductCollectionSerializer(many=True, read_only=True)
    product_tags = ProductTagSerializer(many=True, read_only=True)
    variants = VariantUpdateSerializer(many=True, required=True)
    variant_options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            'product_name', 'product_desc', 'shopify_product_id', 'product_tags', 'product_collections',
            'variants',
            'variant_options')
    def validate_product_collections(self, product_collections):
        if not product_collections:
            CustomValidationError("产品系列不能为空,请在shopify中添加后重新同步")
        return product_collections
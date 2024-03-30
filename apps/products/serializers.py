import copy
import json
import logging
import threading
import time
from pprint import pprint

from apps.core.validators import CustomValidationError
from rest_framework import serializers
from .models import Product, Variant, ProductTag, ProductCollection, Option, OptionValue
from apps.proxy_server.models import Acls, Cidr, ProxyStock
from apps.proxy_server.serializers import ServersGroupSerializer, AclsGroupSerializer, AclGroup, ServerGroup
from apps.proxy_server.models import ServerGroupThrough, ServerCidrThrough, ProductStock
from drf_writable_nested.serializers import WritableNestedModelSerializer
from django.core.cache import caches


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
    variant_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Variant
        fields = ("id",
                  "shopify_variant_id", 'variant_name', 'variant_desc', 'server_group', 'cart_step',
                  'is_active',
                  'variant_price',
                  'variant_stock', 'variant_option1', 'variant_option2', 'variant_option3', "proxy_time")

    # def get_variant_stock(self, obj):
    #     variant_stock = obj.update_stock()
    #     return variant_stock

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if not ret["variant_desc"]:
            ret["variant_desc"] = ''
        # todo 优化
        # ret["variant_stock"] = self.get_variant_stock(instance)
        return ret


def get_cidr(server_group):
    cidrs = []
    if server_group:
        server_ids = ServerGroupThrough.objects.filter(server_group_id=server_group.id).values_list('server_id',
                                                                                                    flat=True)
        for x in ServerCidrThrough.objects.filter(server_id__in=server_ids).all():
            cidrs.append(x.cidr)
        return cidrs
    else:
        return cidrs


class VariantCreateSerializer(serializers.ModelSerializer):
    cart_step = serializers.IntegerField(required=True)
    variant_price = serializers.FloatField(required=True)
    server_group = serializers.PrimaryKeyRelatedField(queryset=ServerGroup.objects.all(), required=True)

    # acl_group = serializers.PrimaryKeyRelatedField(queryset=AclGroup.objects.all(), required=True)

    class Meta:
        model = Variant
        fields = (
            "shopify_variant_id", 'variant_name', 'variant_desc', 'server_group', 'cart_step', 'is_active',
            'variant_price',
            'variant_stock', 'variant_option1', 'variant_option2', 'variant_option3', "proxy_time")

    def create(self, validated_data):
        variant = Variant.objects.create(**validated_data)

        variant.save()
        return variant


class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = ('id', 'tag_name', 'tag_desc')
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
    shopify_variant_id = serializers.CharField(required=False)
    id = serializers.CharField(required=False)

    class Meta:
        model = Variant
        fields = ('id', 'variant_name', 'variant_desc', 'server_group', 'cart_step', 'is_active',
                  'variant_price', 'shopify_variant_id',
                  'variant_stock', 'variant_option1', 'variant_option2', 'variant_option3', "proxy_time")
        extra_kwargs = {
            'shopify_variant_id': {'read_only': True},
            'id': {'read_only': True},
        }

    def get_cidr(self, server_group):
        cidr_ids = []
        if server_group:
            server_group_id = server_group.id

            server_ids = ServerGroupThrough.objects.filter(server_group_id=server_group_id).values_list('server_id',
                                                                                                        flat=True)
            cidr_ids = ServerCidrThrough.objects.filter(server_id__in=server_ids).values_list('cidr_id', flat=True)
            ip_count = Cidr.objects.filter(id__in=cidr_ids).values_list('ip_count', flat=True)
            return cidr_ids, ip_count
        else:
            return cidr_ids, []

    def validate(self, attrs):
        cidr_ids, ip_count = self.get_cidr(attrs.get('server_group'))
        cart_step = attrs.get('cart_step')
        for idx, cidr_id in enumerate(cidr_ids):
            # 如果库存表不存在，就创建
            if not ProxyStock.objects.filter(cidr_id=cidr_id, cart_step=cart_step).exists():
                cart_stock = ip_count[idx] // attrs.get('cart_step')
                porxy_stock = ProxyStock.objects.create(cidr_id=cidr_id,
                                                        ip_stock=ip_count[idx], cart_step=attrs.get('cart_step'),
                                                        cart_stock=cart_stock)
                subnets = porxy_stock.gen_subnets()
                porxy_stock.subnets = ",".join(subnets)
                porxy_stock.available_subnets = porxy_stock.subnets
                porxy_stock.save()
        return attrs

    def save(self, **kwargs):
        return super().save(**kwargs)


class ProductCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCollection
        fields = ('id', 'collection_name', 'collection_desc', 'shopify_collection_id')

    def create(self, validated_data):
        product_collection, _ = ProductCollection.objects.get_or_create(**validated_data)
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
                  'variant_options', "created_at", "lower_price", "active", "old_flag")

    def get_lower_price(self, obj):
        if obj.variants.exists():
            return "$" + str(obj.variants.order_by('variant_price').first().variant_price) + "+"
        else:
            return "$0.0+"

    def to_representation(self, instance):
        cache = caches['default']
        cache_key = f"product_{instance.id}"
        redis_client = cache.client.get_client()
        # if redis_client.hget("products", cache_key):
        #     return json.loads(redis_client.hget("products", cache_key))
        ret = super().to_representation(instance)

        # 获取 variants 和 variant_options
        variants = ret.get('variants', [])
        variant_options = ret.get('variant_options', [])

        # 使用集合进行快速查找
        options = [set(), set(), set()]
        for v in variants:
            if v.get('variant_option1'):
                options[0].add(v.get('variant_option1'))
            if v.get('variant_option2'):
                options[1].add(v.get('variant_option2'))
            if v.get('variant_option3'):
                options[2].add(v.get('variant_option3'))
        variant_options_ret = []
        # 使用列表推导式过滤 variant_options
        for idx, option in enumerate(variant_options):
            option_values = option.get('option_values', [])
            print(option_values)
            filtered_values = [val for val in option_values if val.get('option_value') in options[idx]]
            option['option_values'] = filtered_values
            variant_options_ret.append(option)
        ret['variant_options'] = variant_options_ret
        redis_client.hset("products", cache_key, json.dumps(ret))
        return ret


class CreateProductOtherThread(threading.Thread):
    def __init__(self, product_id, product_collections_data, product_tags_data, variants_data, options_data):
        threading.Thread.__init__(self)
        self.product_id = product_id
        self.product_collections_data = product_collections_data
        self.product_tags_data = product_tags_data
        self.variants_data = variants_data
        self.options_data = options_data

    def run(self):
        create_product_other(self.product_id, self.product_collections_data, self.product_tags_data, self.variants_data,
                             self.options_data)





def create_product_other(product_id, product_collections_data, product_tags_data, variants_data, options_data):
    product = Product.objects.get(id=product_id)
    # 创建option
    for option_data in options_data:
        option_data['product'] = product
        opt = OptionSerializer().create(option_data)
    acls = Acls.objects.all()
    # 创建variant
    for idx, variant_data in enumerate(variants_data):
        variant_data['product'] = product
        v = VariantCreateSerializer().create(variant_data)
        cart_step = variant_data.get('cart_step', 8)
        # ExtendedVariantCreateSerializer().create(variants_data_ext)
        cidrs = get_cidr(variant_data.get('server_group'))
        for acl_i in acls:
            ip_stock_objs = []
            for cidr_i in cidrs:
                v.cidrs.add(cidr_i)
                cart_stock = cidr_i.ip_count // cart_step
                stock_obj, is_create = ProxyStock.objects.get_or_create(cidr=cidr_i, acl=acl_i, cart_step=cart_step)
                if is_create:
                    stock_obj.ip_stock = cidr_i.ip_count
                    stock_obj.cart_stock = cart_stock
                    subnets = stock_obj.gen_subnets()
                    stock_obj.subnets = ",".join(subnets)
                    stock_obj.available_subnets = stock_obj.subnets
                    stock_obj.save()
                stock_obj.soft_delete = False
                stock_obj.save()
                ip_stock_objs.append(stock_obj)
            product_stock = ProductStock.objects.create(product=product, acl_id=acl_i.id,
                                                        option1=variant_data.get('variant_option1'),
                                                        option2=variant_data.get('variant_option2'),
                                                        option3=variant_data.get('variant_option3'),
                                                        cart_step=cart_step, old_variant_id=v.id,
                                                        server_group=variant_data.get('server_group'))
            stock = 0
            for ip_stock_obj in ip_stock_objs:
                product_stock.ip_stocks.add(ip_stock_obj)
                stock += ip_stock_obj.ip_stock
            product_stock.stock = stock
            product_stock.save()
    # 创建product_collection
    for product_collection_data in product_collections_data:
        product_collection = ProductCollectionSerializer().create(product_collection_data)
        product.product_collections.add(product_collection)
    # 创建product_tag
    for product_tag_data in product_tags_data:
        product_tag = ProductTagSerializer().create(product_tag_data)
        product.product_tags.add(product_tag)
    product.valid = True
    product.save()


class ProductCreateSerializer(serializers.ModelSerializer):
    product_collections = ProductCollectionSerializer(many=True, required=True)
    product_tags = ProductTagSerializer(many=True, required=True)
    variants = VariantCreateSerializer(many=True, required=True)
    variant_options = OptionSerializer(many=True, required=True)

    class Meta:
        model = Product
        fields = (
            'product_name', 'product_desc', 'shopify_product_id', 'product_tags', 'product_collections',
            'variants', 'variant_options')

    def validate_product_collections(self, product_collections):
        if not product_collections:
            raise CustomValidationError("产品系列不能为空,请在shopify中添加后重新同步")
        return product_collections

    def create(self, validated_data):  # 先创建variant,再创建product,再add
        variants_data = validated_data.pop('variants')
        product_collections_data = validated_data.pop('product_collections')
        product_tags_data = validated_data.pop('product_tags')
        options_data = validated_data.pop('variant_options')
        product = Product.objects.create(**validated_data)  # 创建其他数据
        CreateProductOtherThread(product.id, product_collections_data, product_tags_data, variants_data,
                                 options_data).start()
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
            'variants', 'active',
            'variant_options')

    def validate_product_collections(self, product_collections):
        if not product_collections:
            CustomValidationError("产品系列不能为空,请在shopify中添加后重新同步")
        return product_collections

    def validate(self, attrs):

        variants = attrs.get('variants')
        is_active = False
        if variants:
            for variant in variants:
                if variant.get('is_active'):
                    is_active = True
                    break
        attrs['active'] = is_active
        return attrs

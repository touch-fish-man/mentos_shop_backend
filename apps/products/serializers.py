from pprint import pprint

from rest_framework import serializers
from .models import Product, Variant, ProductTag, ProductCollection, Option, OptionValue
from apps.proxy_server.models import Acls, Cidr, ProxyStock
from apps.proxy_server.serializers import ServersGroupSerializer,AclsGroupSerializer,AclGroup,ServerGroup
from apps.proxy_server.models import ServerGroupThrough,ServerCidrThrough


class OptionValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionValue
        fields = ('option_value',)


class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = ('tag_name', 'tag_desc')

    def create(self, validated_data):
        if ProductTag.objects.filter(tag_name=validated_data.get('tag_name')).exists():
            tag = ProductTag.objects.get(tag_name=validated_data.get('tag_name'))
            for k, v in validated_data.items():
                setattr(tag, k, v)
            tag.save()
        else:
            tag = ProductTag.objects.create(**validated_data)
        return tag


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
        fields = (
            "shopify_variant_id", 'variant_name', 'variant_desc', 'server_group', 'acl_group', 'cart_step', 'is_active',
            'variant_price',
            'variant_stock', 'variant_option1', 'variant_option2', 'variant_option3')

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
            'variant_stock', 'variant_option1', 'variant_option2', 'variant_option3')
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
        variant_stock = sum(ip_count)
        variant.variant_stock =variant_stock
        variant.save()
        acl_group_id=validated_data.get('acl_group').id
        for idx,cidr_id in enumerate(cidr_ids):
            cart_stock=ip_count[idx]//validated_data.get('cart_step')
            ProxyStock.objects.create(cidr_id=cidr_id, acl_group_id=acl_group_id, ip_stock=ip_count[idx], variant_id=variant.id,cart_step=validated_data.get('cart_step'),cart_stock=cart_stock)
        return variant

class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = ('id','tag_name', 'tag_desc')

    def create(self, validated_data):
        if ProductTag.objects.filter(tag_name=validated_data.get('tag_name')).exists():
            product_tag = ProductTag.objects.get(tag_name=validated_data.get('tag_name'))
            for k, v in validated_data.items():
                setattr(product_tag, k, v)
            product_tag.save()
        else:
            product_tag = ProductTag.objects.create(**validated_data)
        return product_tag


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

    class Meta:
        model = Product
        fields = ("id",
                  'product_name', 'product_desc', 'shopify_product_id', 'product_tags', 'product_collections',
                  'variants',
                  'variant_options',"created_at")


class ProductCreateSerializer(serializers.ModelSerializer):
    product_collections = ProductCollectionSerializer(many=True)
    product_tags = ProductTagSerializer(many=True)
    variants = VariantCreateSerializer(many=True)
    variant_options = OptionSerializer(many=True)

    class Meta:
        model = Product
        fields = (
            'product_name', 'product_desc', 'shopify_product_id', 'product_tags', 'product_collections',
            'variants',
            'variant_options')

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

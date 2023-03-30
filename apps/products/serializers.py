from rest_framework import serializers
from .models import Product, Variant, VariantAttribute


class VariantAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantAttribute
        fields = ('attribute', 'attribute_value')


class VariantSerializer(serializers.ModelSerializer):
    attributes = VariantAttributeSerializer(many=True, read_only=True)

    class Meta:
        model = Variant
        fields = ('variant_name', 'price', 'stock', 'attributes')


class ProductSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('product_name', 'product_desc', 'product_tags','variants','product_collection')

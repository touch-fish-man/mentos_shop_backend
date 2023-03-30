from apps.core.models import BaseModel
from django.db import models


class Product(BaseModel):
    product_name = models.CharField(max_length=255, verbose_name='产品名')
    product_desc = models.TextField(verbose_name='描述')
    shopify_product_id = models.CharField(max_length=255, verbose_name='shopify产品id')
    product_tags = models.CharField(max_length=255, verbose_name='产品标签')
    product_collection = models.CharField(max_length=255, verbose_name='产品集合')

    def variants(self):
        variants = Variant.objects.filter(product=self)
        for variant in variants:
            variant.attributes = VariantAttribute.objects.filter(variant=variant)
        return variants


class ProductTag(BaseModel):
    product_tag = models.CharField(max_length=255, verbose_name='产品标签')
    tag_desc = models.TextField(verbose_name='描述')
    shopify_tag_id = models.CharField(max_length=255, verbose_name='shopify标签id')


class ProductCollection(BaseModel):
    product_collection = models.CharField(max_length=255, verbose_name='产品集合')
    collection_desc = models.TextField(verbose_name='描述')
    shopify_collection_id = models.CharField(max_length=255, verbose_name='shopify集合id')


class Attribute(BaseModel):
    attribute_name = models.CharField(max_length=255, verbose_name='属性名')
    attribute_type = models.CharField(max_length=255, verbose_name='属性类型')


class AttributeValue(BaseModel):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    attribute_value = models.CharField(max_length=255, verbose_name='属性值')


class Variant(BaseModel):
    shopify_variant_id = models.CharField(max_length=255, verbose_name='shopify变体id')
    variant_name = models.CharField(max_length=255)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant_desc = models.TextField(verbose_name='描述')
    server_group = models.CharField(max_length=255, verbose_name='服务器组')
    acl_group = models.CharField(max_length=255, verbose_name='acl组')
    cart_step = models.IntegerField(default=1, verbose_name='购物车步长')
    is_active = models.BooleanField(default=True, verbose_name='是否上架')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    stock = models.IntegerField(verbose_name='库存')


class VariantAttribute(BaseModel):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)
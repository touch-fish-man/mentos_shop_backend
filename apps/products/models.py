from apps.core.models import BaseModel
from django.db import models


class ProductTag(BaseModel):
    tag_name = models.CharField(max_length=255, verbose_name='标签名')
    tag_desc = models.TextField(verbose_name='标签描述', blank=True, null=True)


class ProductCollection(BaseModel):
    """
    商品系列
    """
    collection_name = models.CharField(max_length=255, verbose_name='系列名称')
    collection_desc = models.TextField(verbose_name='描述')
    shopify_collection_id = models.CharField(max_length=255, verbose_name='shopify商品系列id')


class OptionValue(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='option_values')
    option = models.ForeignKey('Option', on_delete=models.CASCADE, related_name='option_values')
    option_value = models.CharField(max_length=255, verbose_name='选项值')


class Option(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='options',verbose_name='商品')
    option_name = models.CharField(max_length=255, verbose_name='选项名')
    option_type = models.CharField(max_length=255, verbose_name='选项类型', blank=True, null=True)
    shopify_option_id = models.CharField(max_length=255, verbose_name='shopify选项id')

class Variant(BaseModel):
    """
    商品变体
    """
    CART_STEP = (
        (8, 8),
        (16, 16),
        (32, 32),
        (64, 64),
        (128, 128),
        (256, 256),
        (512, 512),
        (1024, 1024)
    )

    shopify_variant_id = models.CharField(max_length=255, verbose_name='shopify变体id')
    variant_name = models.CharField(max_length=255, verbose_name='变体名')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='variants')
    # 可以为空
    variant_desc = models.TextField(verbose_name='描述', blank=True, null=True)
    server_group = models.ForeignKey('proxy_server.ServerGroup', verbose_name='服务器组', blank=True, null=True, on_delete=models.CASCADE)
    acl_group = models.ForeignKey('proxy_server.AclGroup', verbose_name='acl组', blank=True, null=True, on_delete=models.CASCADE)
    cart_step = models.IntegerField(default=8, verbose_name='购物车步长', choices=CART_STEP)
    is_active = models.BooleanField(default=True, verbose_name='是否上架', blank=True, null=True)
    variant_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    variant_stock = models.IntegerField(verbose_name='库存',default=0)
    variant_option1 = models.CharField(max_length=255, verbose_name='选项1', blank=True, null=True)
    variant_option2 = models.CharField(max_length=255, verbose_name='选项2', blank=True, null=True)
    variant_option3 = models.CharField(max_length=255, verbose_name='选项3', blank=True, null=True)


class Product(BaseModel):
    """
    商品
    """
    product_name = models.CharField(max_length=255, verbose_name='产品名')
    product_desc = models.TextField(verbose_name='描述', blank=True, null=True)
    shopify_product_id = models.CharField(max_length=255, verbose_name='shopify产品id')
    product_tags = models.ManyToManyField(ProductTag,verbose_name='标签')
    product_collections = models.ManyToManyField(ProductCollection,verbose_name='系列')
    # variants = models.ManyToManyField(Variant)
    # variant_options = models.ManyToManyField(Option)

    def variants(self):
        return Variant.objects.filter(product_id=self.id)

    def variant_options(self):
        return Option.objects.filter(product_id=self.id)
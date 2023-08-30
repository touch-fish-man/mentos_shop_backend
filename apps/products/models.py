import logging
import traceback

from apps.core.models import BaseModel
from django.db import models

from apps.proxy_server.models import ProxyStock, ServerGroupThrough, ServerCidrThrough, Cidr


class ProductTag(BaseModel):
    tag_name = models.CharField(max_length=255, verbose_name='标签名')
    tag_desc = models.TextField(verbose_name='标签描述', blank=True, null=True)
    soft_delete = models.BooleanField(default=False, verbose_name='软删除')

    def delete(self, using=None, keep_parents=False):
        if ProductTagRelation.objects.filter(product_tag=self.id).exists():
            self.soft_delete = True
            self.save()
        else:
            return super().delete(using=None, keep_parents=False)


class ProductCollection(BaseModel):
    """
    商品系列
    """
    collection_name = models.CharField(max_length=255, verbose_name='系列名称')
    collection_desc = models.TextField(verbose_name='描述')
    shopify_collection_id = models.CharField(max_length=255, verbose_name='shopify商品系列id')
    soft_delete = models.BooleanField(default=False, verbose_name='软删除')

    def delete(self, using=None, keep_parents=False):
        if ProductCollectionRelation.objects.filter(product_collection=self.id).exists():
            self.soft_delete = True
            self.save()
        else:
            return super().delete(using=None, keep_parents=False)


class OptionValue(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='option_values')
    option = models.ForeignKey('Option', on_delete=models.CASCADE, related_name='option_values')
    option_value = models.CharField(max_length=255, verbose_name='选项值')


class Option(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='options', verbose_name='商品')
    option_name = models.CharField(max_length=255, verbose_name='选项名')
    option_type = models.CharField(max_length=255, verbose_name='选项类型', blank=True, null=True)  # 时间 1 其他0
    shopify_option_id = models.CharField(max_length=255, verbose_name='shopify选项id')


class Variant(BaseModel):
    """
    商品变体
    """
    CART_STEP = (
        (1, 1),
        (8, 8),
        (16, 16),
        (32, 32),
        (64, 64),
        (128, 128),
        (256, 256),
        (512, 512),
        (1024, 1024)
    )
    stock_ids=[]

    shopify_variant_id = models.CharField(max_length=255, verbose_name='shopify变体id')
    variant_name = models.CharField(max_length=255, verbose_name='变体名')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='variants')
    # 可以为空
    variant_desc = models.TextField(verbose_name='描述', blank=True, null=True)
    server_group = models.ForeignKey('proxy_server.ServerGroup', verbose_name='服务器组', blank=True, null=True,
                                     on_delete=models.CASCADE)
    acl_group = models.ForeignKey('proxy_server.AclGroup', verbose_name='acl组', blank=True, null=True,
                                  on_delete=models.CASCADE)
    cart_step = models.IntegerField(default=8, verbose_name='购物车步长', choices=CART_STEP)
    is_active = models.BooleanField(default=True, verbose_name='是否上架', blank=True, null=True)
    variant_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    variant_stock = models.IntegerField(verbose_name='库存', default=0)  # ip数量
    variant_option1 = models.CharField(max_length=255, verbose_name='选项1', blank=True, null=True)
    variant_option2 = models.CharField(max_length=255, verbose_name='选项2', blank=True, null=True)
    variant_option3 = models.CharField(max_length=255, verbose_name='选项3', blank=True, null=True)
    proxy_time = models.IntegerField(verbose_name='代理时间', default=30)

    def get_stock(self):
        variant_stock = 0
        cart_step = self.cart_step
        acl_group = self.acl_group
        server_group = self.server_group
        cidr_ids, ip_count = self.get_cidr(server_group)
        stocks = ProxyStock.objects.filter(cidr_id__in=cidr_ids, cart_step=cart_step, acl_group=acl_group)
        stocks_dict = {stock.cidr_id: stock for stock in stocks}
        print(stocks_dict)

        for idx,cidr_id in enumerate(cidr_ids):
            stock_obj = stocks_dict.get(cidr_id)
            if stock_obj:
                self.stock_ids.append(stock_obj.id)
                variant_stock += stock_obj.ip_stock
            else:
                # 不存在则创建
                logging.info(self.id)
                logging.info(cidr_ids)
                logging.info(ip_count)
                logging.info(idx)
                cart_stock =ip_count[idx] // cart_step
                porxy_stock=ProxyStock.objects.create(cidr_id=cidr_id, cart_step=cart_step, acl_group=acl_group, ip_stock=ip_count[idx], cart_stock=cart_stock)
                subnets = porxy_stock.gen_subnets()
                porxy_stock.subnets = ",".join(subnets)
                porxy_stock.available_subnets = porxy_stock.subnets
                porxy_stock.save()
                variant_stock += ip_count[idx]
                self.stock_ids.append(porxy_stock.id)
        return variant_stock

    def get_cidr(self, server_group):
        cidr_ids = []
        if server_group:

            server_ids = ServerGroupThrough.objects.filter(server_group_id=server_group.id).values_list('server_id',
                                                                                                        flat=True)
            cidr_ids = ServerCidrThrough.objects.filter(server_id__in=server_ids).values_list('cidr_id', flat=True)
            ip_count = Cidr.objects.filter(id__in=cidr_ids).values_list('id','ip_count')
            ip_count_dict = dict(ip_count)
            ip_count = [ip_count_dict.get(cidr_id) for cidr_id in cidr_ids]

            return cidr_ids, ip_count
        else:
            return cidr_ids, []


    def update_stock(self):
        get_stock = self.get_stock()
        self.variant_stock = get_stock
        self.save()
        return get_stock

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.id:
            get_stock = self.get_stock()
            self.variant_stock = get_stock
        super().save(force_insert=False, force_update=False, using=None,
                     update_fields=None)


class Product(BaseModel):
    """
    商品
    """
    product_name = models.CharField(max_length=255, verbose_name='产品名')
    product_desc = models.TextField(verbose_name='描述', blank=True, null=True)
    shopify_product_id = models.CharField(max_length=255, verbose_name='shopify产品id')
    product_tags = models.ManyToManyField(ProductTag, verbose_name='标签', through='ProductTagRelation')
    product_collections = models.ManyToManyField(ProductCollection, verbose_name='系列',
                                                 through='ProductCollectionRelation')
    soft_delete = models.BooleanField(default=False, verbose_name='软删除', blank=True, null=True)

    # variants = models.ManyToManyField(Variant)
    # variant_options = models.ManyToManyField(Option)
    active = models.BooleanField(default=True, verbose_name='是否上架', blank=True, null=True)
    def delete(self, using=None, keep_parents=False):
        self.soft_delete = True
        self.save()

    def variants(self):
        return Variant.objects.filter(product_id=self.id)
    @property
    def is_active(self):
        return Variant.objects.filter(product_id=self.id, is_active=True).exists()

    def variant_options(self):
        return Option.objects.filter(product_id=self.id)
    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert=False, force_update=False, using=None,
                     update_fields=None)


class ProductTagRelation(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_tag = models.ForeignKey(ProductTag, on_delete=models.CASCADE)


class ProductCollectionRelation(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_collection = models.ForeignKey(ProductCollection, on_delete=models.CASCADE)

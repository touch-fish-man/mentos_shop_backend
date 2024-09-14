import logging
import traceback

from django.core.cache import cache
from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver

from apps.core.models import BaseModel
from django.db import models, transaction
from django.db import IntegrityError

from apps.core.validators import CustomValidationError
from apps.proxy_server.models import ProxyStock, ServerGroupThrough, ServerCidrThrough, Cidr, Acls, ProductStock
from django.db import transaction

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

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        cache_key = 'product_tags'
        if cache.get(cache_key):
            cache.delete(cache_key)
        return super().save(force_insert, force_update, using, update_fields)


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

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        cache_key = 'product_collections'
        if cache.get(cache_key):
            cache.delete(cache_key)
        return super().save(force_insert, force_update, using, update_fields)


class OptionValue(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='option_values')
    option = models.ForeignKey('Option', on_delete=models.CASCADE, related_name='option_values')
    option_value = models.CharField(max_length=255, verbose_name='选项值')


class Option(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='options', verbose_name='商品')
    option_name = models.CharField(max_length=255, verbose_name='选项名')
    option_type = models.CharField(max_length=255, verbose_name='选项类型', blank=True, null=True)  # 时间 1 其他0
    shopify_option_id = models.CharField(max_length=255, verbose_name='shopify选项id')


class VariantCidrThrough(BaseModel):
    variant = models.ForeignKey('Variant', on_delete=models.CASCADE, blank=True, null=True,
                                verbose_name='变体')
    cidr = models.ForeignKey('proxy_server.Cidr', on_delete=models.CASCADE, blank=True, null=True,

                             verbose_name='CIDR')

    class Meta:
        db_table = 'variant_cidr_through'
        verbose_name = '变体与CIDR关系'
        verbose_name_plural = '变体与CIDR关系'


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
    stock_ids = []

    shopify_variant_id = models.CharField(max_length=255, verbose_name='shopify变体id')
    variant_name = models.CharField(max_length=255, verbose_name='变体名')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='variants')
    # 可以为空
    variant_desc = models.TextField(verbose_name='描述', blank=True, null=True)
    server_group = models.ForeignKey('proxy_server.ServerGroup', verbose_name='服务器组', blank=True, null=True,
                                     on_delete=models.PROTECT, related_name='variants')
    acl_group = models.ForeignKey('proxy_server.AclGroup', verbose_name='acl组', blank=True, null=True,
                                  on_delete=models.CASCADE)
    cart_step = models.IntegerField(default=8, verbose_name='购物车步长', choices=CART_STEP)
    is_active = models.BooleanField(default=True, verbose_name='是否上架', blank=True, null=True)
    variant_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    variant_stock = models.IntegerField(verbose_name='库存', default=999)  # ip数量
    variant_option1 = models.CharField(max_length=255, verbose_name='选项1', blank=True, null=True)
    variant_option2 = models.CharField(max_length=255, verbose_name='选项2', blank=True, null=True)
    variant_option3 = models.CharField(max_length=255, verbose_name='选项3', blank=True, null=True)
    proxy_time = models.IntegerField(verbose_name='代理时间', default=30)
    cidrs = models.ManyToManyField('proxy_server.Cidr', through='VariantCidrThrough', related_name='cidrs')
    # def save(
    #     self, force_insert=False, force_update=False, using=None, update_fields=None
    # ):
    #     logging.info(self.server_group)
    #     if self.server_group:
    #         cidrs = self.server_group.get_cidrs()
    #         logging.info('cidrs:%s' % cidrs)
    #         if cidrs:
    #             self.cidrs.clear()
    #             for cidr in cidrs:
    #                 logging.info('add cidr:%s' % cidr)
    #                 self.cidrs.add(cidr)
    #     return super().save(force_insert, force_update, using, update_fields)


    def update_ip_stock(self):
        logging.info('Update Variant IP Stock: %s' % self.id)
        self.refresh_from_db()  # 确保获取最新数据

        # 查询变体的cidr
        cidrs = list(self.cidrs.all())  # 使用 list() 提前获取，减少查询次数
        acls = list(Acls.objects.all())  # 在循环外获取所有ACL，减少查询次数

        # 使用事务来确保数据操作的原子性
        with transaction.atomic():
            # 批量创建的对象列表
            proxy_stocks_to_create = []
            proxy_stocks_to_update = []

            # 准备需要创建和更新的 ProxyStock 实例
            for cidr in cidrs:
                exclude_acl_list = cidr.list_exclude_acl()

                for acl in acls:
                    # 检查是否已经存在 ProxyStock 对象
                    existing_stock = ProxyStock.objects.filter(cidr=cidr, acl=acl, cart_step=self.cart_step).first()

                    if existing_stock:
                        # 如果存在则更新
                        existing_stock.soft_delete = False
                        if acl.id in exclude_acl_list:
                            existing_stock.exclude_label = True
                        proxy_stocks_to_update.append(existing_stock)
                    else:
                        # 如果不存在则创建新的
                        new_stock = ProxyStock(
                            cidr=cidr,
                            acl=acl,
                            cart_step=self.cart_step,
                            ip_stock=cidr.ip_count,
                            cart_stock=cidr.ip_count // self.cart_step,
                            subnets=",".join(cidr.gen_subnets(self.cart_step)),
                            available_subnets=",".join(cidr.gen_subnets(self.cart_step)),
                            soft_delete=False,
                            exclude_label=(acl.id in exclude_acl_list)
                        )
                        proxy_stocks_to_create.append(new_stock)

            # 批量创建新的 ProxyStock 实例
            ProxyStock.objects.bulk_create(proxy_stocks_to_create)
            logging.info('update_ip_stock: create %s proxy_stocks' % len(proxy_stocks_to_create))
            logging.info('update_ip_stock: update %s proxy_stocks' % len(proxy_stocks_to_update))
            # 批量更新现有的 ProxyStock 实例
            ProxyStock.objects.bulk_update(
                proxy_stocks_to_update,
                fields=["soft_delete", "exclude_label"]
            )

            # 更新旧的 ProductStock 实例
            old_product_stocks = ProductStock.objects.filter(variant_id=self.id)
            old_product_stocks_to_update = []

            for old_product_stock in old_product_stocks:
                old_product_stock.server_group = self.server_group
                old_product_stocks_to_update.append(old_product_stock)

            # 批量更新 ProductStock 实例
            ProductStock.objects.bulk_update(old_product_stocks_to_update, fields=["server_group"])
            for old_product_stock in old_product_stocks_to_update:
                old_product_stock.save() # 触发库存更新



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
    variant_options = models.ManyToManyField(Option, verbose_name='选项', through='OptionValue',related_name='product_variants')
    active = models.BooleanField(default=True, verbose_name='是否上架', blank=True, null=True)
    valid = models.BooleanField(default=False, verbose_name='是否有效', blank=True, null=True)
    old_flag = models.BooleanField(default=False, verbose_name='是否旧商品', blank=True, null=True)

    @property
    def is_active(self):
        return Variant.objects.filter(product_id=self.id, is_active=True).exists()


class ProductTagRelation(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_tag = models.ForeignKey(ProductTag, on_delete=models.CASCADE)


class ProductCollectionRelation(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_collection = models.ForeignKey(ProductCollection, on_delete=models.CASCADE)



@receiver(m2m_changed, sender=Variant.cidrs.through)
def update_variant_stock(sender, instance, action, reverse, model, pk_set, **kwargs):
    logging.info('tirgger update_variant_stock,action:%s' % action)
    if action in ['post_add', 'post_remove', 'post_clear']:
        # cidr更新产品库存
        for p_s in instance.product_stocks.all():
            p_s.save()

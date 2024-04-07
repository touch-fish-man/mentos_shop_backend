import json

from apps.products.models import Product, ProductCollection, ProductTag, Variant

from apps.products.serializers import ProductSerializer, VariantSerializer, ProductCollectionSerializer, \
    ProductTagSerializer, \
    ProductCreateSerializer, ProductUpdateSerializer
from apps.products.services import get_stock, get_variant_info
from apps.core.viewsets import ComModelViewSet
from apps.utils.shopify_handler import ShopifyClient, SyncClient
from rest_framework.decorators import action
from apps.core.json_response import SuccessResponse, ErrorResponse, LimitOffsetResponse
from django.conf import settings
from apps.core.permissions import IsAuthenticated, IsSuperUser
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.db import connection
from django.db.models import Prefetch


class ProductViewSet(ComModelViewSet):
    """
    商品列表
    list:列表
    create:创建
    update:更新
    retrieve:详情
    destroy:删除
    get_recommend_product:获取推荐商品
    """
    queryset = Product.objects.filter(soft_delete=False).all().prefetch_related(
        'product_collections', 'product_tags',Prefetch('variants', queryset=Variant.objects.all()))
    serializer_class = ProductSerializer
    create_serializer_class = ProductCreateSerializer
    update_serializer_class = ProductUpdateSerializer
    search_fields = ['product_name', 'product_desc']
    filter_fields = '__all__'
    filterset_fields = '__all__'
    permission_classes = [IsSuperUser]
    unauthenticated_actions = ['list', 'get_recommend_product']

    def get_permissions(self):
        if self.action in ['list', "get_recommend_product", "stock", "price", "variant_info"]:
            return []
        return super(ProductViewSet, self).get_permissions()

    @action(methods=['get'], detail=False, url_path='get_product_from_shopify', url_name='get_product_from_shopify')
    def get_product_from_shopify(self, request):
        cache_client = cache.client.get_client()
        cache_key = 'shopify_product'
        cache_data = cache_client.hgetall(cache_key)
        if cache_data:
            data=[]
            for key in cache_data:
                data.append(json.loads(cache_data[key]))
            return SuccessResponse(data=data)
        shop_url = settings.SHOPIFY_SHOP_URL
        api_key = settings.SHOPIFY_API_KEY
        api_scert = settings.SHOPIFY_API_SECRET
        private_app_password = settings.SHOPIFY_APP_KEY
        shopify_client = ShopifyClient(shop_url, api_key, api_scert, private_app_password)
        product_dict = shopify_client.get_products(format=True)
        for product in product_dict:
            cache_client.hset(cache_key, product['shopify_product_id'], json.dumps(product))
        return SuccessResponse(data=product_dict)

    @action(methods=['get'], detail=False, url_path='get_recommend_product', url_name='get_recommend_product')
    def get_recommend_product(self, request):
        """
        获取推荐商品
        :param request:
        """
        # 使用redi缓存

        tags = request.query_params.get('tags')
        if not tags:
            return ErrorResponse(msg='tags不能为空')
        tags = tags.split(',')
        key = 'recommend_product' + str("".join(tags))
        # 获取缓存数据
        get_data = cache.get(key)
        get_data = None
        if get_data:
            return SuccessResponse(data=get_data)
        else:
            products = Product.objects.filter(product_tags__in=tags, soft_delete=False).distinct()
            serializer = self.get_serializer(products, many=True)
            get_data = serializer.data
            cache.set(key, get_data, timeout=60 * 60 * 8)
            # 获取分页数据
            page = self.paginate_queryset(products)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            return SuccessResponse(data=serializer.data)

    @action(methods=['post'], detail=False, url_path='stock', url_name='stock')
    def stock(self, request):
        product_id = request.data.get('product_id')
        option_selected = request.data.get("option_selected", {})
        if len(option_selected) < 3:
            return ErrorResponse(msg='option_selected参数错误')
        variant_option1 = option_selected.get('option1', "")
        variant_option2 = option_selected.get('option2', "")
        variant_option3 = option_selected.get('option3', "")
        acl_selected = option_selected.get('acl_selected', [])
        if not product_id:
            return ErrorResponse(msg='product_id不能为空')
        product_stock = get_stock(product_id, variant_option1, variant_option2, variant_option3)
        return SuccessResponse(data=product_stock)

    @action(methods=['post'], detail=False, url_path='variant_info', url_name='variant_info')
    def variant_info(self, request):
        option_selected = request.data.get("option_selected", {})
        product_id = request.data.get('product_id')
        if len(option_selected) < 3:
            return ErrorResponse(msg='option_selected参数错误')
        variant_option1 = option_selected.get('option1', "")
        variant_option2 = option_selected.get('option2', "")
        variant_option3 = option_selected.get('option3', "")
        acl_selected = option_selected.get('acl_selected', [])
        if not product_id:
            return ErrorResponse(msg='product_id不能为空')
        variant_info = get_variant_info(product_id, variant_option1, variant_option2, variant_option3, acl_selected)
        return SuccessResponse(data=variant_info)

    def list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            self.queryset = self.queryset.filter(old_flag=False).filter(valid=True)
        page = self.paginate_queryset(self.queryset)
        serializer = self.get_serializer(page, many=True)
        get_data = serializer.data

        if page is not None:
            return self.get_paginated_response(get_data)
        else:
            return SuccessResponse(data=get_data)


class ProductCollectionViewSet(ComModelViewSet):
    """
    商品系列
    list:列表
    create:创建
    update:更新
    retrieve:详情
    destroy:删除
    sync_collection:从shopify同步系列
    """
    permission_classes = [IsSuperUser]
    queryset = ProductCollection.objects.filter(soft_delete=False).all()
    serializer_class = ProductCollectionSerializer
    unauthenticated_actions = ['list']

    @action(methods=['get'], detail=False, url_path='sync_collection', url_name='sync_collection')
    def sync_collection(self, request):
        shop_url = settings.SHOPIFY_SHOP_URL
        api_key = settings.SHOPIFY_API_KEY
        api_scert = settings.SHOPIFY_API_SECRET
        shopify_app_key = settings.SHOPIFY_APP_KEY
        shopify_client_sync = SyncClient(shop_url, api_key, api_scert, shopify_app_key)
        sync_ret = shopify_client_sync.sync_product_collections()
        if sync_ret:
            return SuccessResponse(msg='同步成功')
        else:
            return ErrorResponse(msg='同步失败')

    def list(self, request, *args, **kwargs):
        # 使用redi缓存
        cache_key = 'product_collections'
        data = cache.get(cache_key)
        if not data:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                cache.set(cache_key, data, timeout=60 * 60 * 24)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            cache.set(cache_key, data, timeout=60 * 60 * 24)
            return LimitOffsetResponse(data=data, msg="Success")
        return LimitOffsetResponse(data=data, msg="Success")

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = []
        return super(ProductCollectionViewSet, self).get_permissions()


class ProductTagViewSet(ComModelViewSet):
    """
    商品标签
    list:列表
    create:创建
    update:更新
    retrieve:详情
    destroy:删除
    sync_tags:从shopify同步商品标签

    """
    queryset = ProductTag.objects.filter(soft_delete=False).all()
    serializer_class = ProductTagSerializer
    permission_classes = [IsSuperUser]
    unauthenticated_actions = ['list']

    @action(methods=['get'], detail=False, url_path='sync_tags', url_name='sync_tags')
    def sync_tags(self, request):
        shop_url = settings.SHOPIFY_SHOP_URL
        api_key = settings.SHOPIFY_API_KEY
        api_scert = settings.SHOPIFY_API_SECRET
        shopify_app_key = settings.SHOPIFY_APP_KEY
        shopify_client_sync = SyncClient(shop_url, api_key, api_scert, shopify_app_key)
        sync_ret = shopify_client_sync.sync_product_tags()
        if sync_ret:
            return SuccessResponse(msg='同步成功')
        else:
            return ErrorResponse(msg='同步失败')

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = []
        return super(ProductTagViewSet, self).get_permissions()

    def list(self, request, *args, **kwargs):
        # 使用redis缓存
        cache_key = 'product_tags'
        data = cache.get(cache_key)
        data = None

        if not data:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                cache.set(cache_key, data, timeout=60 * 60 * 24)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            cache.set(cache_key, data, timeout=60 * 60 * 24)
            return LimitOffsetResponse(data=data, msg="Success")
        return LimitOffsetResponse(data=data, msg="Success")

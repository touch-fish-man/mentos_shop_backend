
from .models import Product, Variant, ProductCollection, ProductTag
from .serializers import ProductSerializer, VariantSerializer, ProductCollectionSerializer, ProductTagSerializer, \
    ProductCreateSerializer
from apps.core.viewsets import ComModelViewSet
from apps.utils.shopify_handler import ShopifyClient,SyncClient
from rest_framework.decorators import action
from apps.core.json_response import SuccessResponse, ErrorResponse
from django.conf import settings
from apps.core.permissions import IsAuthenticated,IsSuperUser
from rest_framework.permissions import AllowAny
class ProductViewSet(ComModelViewSet):
    """
    商品列表
    list:列表
    create:创建
    update:更新
    retrieve:详情
    destroy:删除
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    create_serializer_class = ProductCreateSerializer
    search_fields = '__all__'
    filter_fields = '__all__'
    filterset_fields = '__all__'
    permission_classes = [IsSuperUser]
    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [AllowAny]
        return super(ProductViewSet, self).get_permissions()

    @action(methods=['get'], detail=False, url_path='get_product_from_shopify', url_name='get_product_from_shopify')
    def get_product_from_shopify(self, request):
        shop_url = settings.SHOPIFY_SHOP_URL
        api_key = settings.SHOPIFY_API_KEY
        api_scert = settings.SHOPIFY_API_SECRET
        private_app_password = settings.SHOPIFY_APP_KEY
        shopify_client = ShopifyClient(shop_url, api_key, api_scert, private_app_password)
        product_dict = shopify_client.get_products(format=True)
        return SuccessResponse(data=product_dict)



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
    queryset = ProductCollection.objects.all()
    serializer_class = ProductCollectionSerializer
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
    queryset = ProductTag.objects.all()
    serializer_class = ProductTagSerializer
    permission_classes = [IsSuperUser]
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
            return []
        return super(ProductTagViewSet, self).get_permissions()
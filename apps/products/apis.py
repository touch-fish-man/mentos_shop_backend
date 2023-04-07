from rest_framework import viewsets
from rest_framework.views import APIView
from .models import Product, Variant, ProductCollection, ProductTag
from .serializers import ProductSerializer, VariantSerializer, ProductCollectionSerializer, ProductTagSerializer, \
    ProductCreateSerializer
from apps.core.viewsets import ComModelViewSet
from apps.utils.shopify_handler import ShopifyClient
from rest_framework.decorators import action
from apps.core.json_response import SuccessResponse
from django.conf import settings


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

    @action(methods=['get'], detail=False, url_path='get_product_from_shopify', url_name='get_product_from_shopify')
    def get_product_from_shopify(self, request):
        shop_url = settings.SHOPIFY_SHOP_URL
        api_version = '2023-01'
        api_key = settings.SHOPIFY_API_KEY
        api_scert = settings.SHOPIFY_API_SECRET
        private_app_password = settings.SHOPIFY_PRIVATE_APP_PASSWORD
        shopify_client = ShopifyClient(shop_url, api_version, api_key, api_scert, private_app_password)
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
    """
    queryset = ProductCollection.objects.all()
    serializer_class = ProductCollectionSerializer
    @action(methods=['get'], detail=False, url_path='get_collection_from_shopify', url_name='get_collection_from_shopify')
    def get_collection_from_shopify(self, request):
        shop_url = settings.SHOPIFY_SHOP_URL
        api_version = '2023-01'
        api_key = settings.SHOPIFY_API_KEY
        api_scert = settings.SHOPIFY_API_SECRET
        private_app_password = settings.SHOPIFY_PRIVATE_APP_PASSWORD
        shopify_client = ShopifyClient(shop_url, api_version, api_key, api_scert, private_app_password)
        productcollection = shopify_client.get_product_collections()
        return SuccessResponse(data=productcollection)


class ProductTagViewSet(ComModelViewSet):
    """
    商品标签
    list:列表
    create:创建
    update:更新
    retrieve:详情
    destroy:删除
    """
    queryset = ProductTag.objects.all()
    serializer_class = ProductTagSerializer
    @action(methods=['get'], detail=False, url_path='get_tags_from_shopify', url_name='get_tags_from_shopify')
    def get_tags_from_shopify(self, request):
        shop_url = settings.SHOPIFY_SHOP_URL
        api_version = '2023-01'
        api_key = settings.SHOPIFY_API_KEY
        api_scert = settings.SHOPIFY_API_SECRET
        private_app_password = settings.SHOPIFY_PRIVATE_APP_PASSWORD
        shopify_client = ShopifyClient(shop_url, api_version, api_key, api_scert, private_app_password)
        product_tags = shopify_client.get_product_tags()
        return SuccessResponse(data=product_tags)

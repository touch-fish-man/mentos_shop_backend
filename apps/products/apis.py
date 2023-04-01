from rest_framework import viewsets
from .models import Product, Variant, ProductCollection, ProductTag
from .serializers import ProductSerializer, VariantSerializer, ProductCollectionSerializer, ProductTagSerializer, \
    ProductCreateSerializer
from apps.core.viewsets import ComModelViewSet
from apps.utils.shopify_handler import ShopifyClient
from rest_framework.decorators import action
from apps.core.json_response import SuccessResponse


class ProductViewSet(ComModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    create_serializer_class = ProductCreateSerializer
    search_fields = ('product_name', 'product_desc', 'product_tags', 'product_collections')
    filter_fields = ('product_name', 'product_desc', 'product_tags', 'product_collections')

    @action(methods=['get'], detail=False, url_path='get_product_from_shopify', url_name='get_product_from_shopify')
    def get_product_from_shopify(self, request):
        shop_url = 'https://mentosproxy.myshopify.com/'
        api_version = '2023-01'
        api_key = 'dd6b4fd6efe094ef3567c61855f11385'
        api_scert = 'f729623ef6a576808a5e83d426723fc1'
        private_app_password = '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'
        shopify_client = ShopifyClient(shop_url, api_version, api_key, api_scert, private_app_password)
        product_dict = shopify_client.get_products(format=True)
        return SuccessResponse(data=product_dict)


class ProductCollectionViewSet(ComModelViewSet):
    queryset = ProductCollection.objects.all()
    serializer_class = ProductCollectionSerializer


class ProductTagViewSet(ComModelViewSet):
    queryset = ProductTag.objects.all()
    serializer_class = ProductTagSerializer

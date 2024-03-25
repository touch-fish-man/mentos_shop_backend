from django.urls import path
from .views import OrdersApi,OrderCallbackApi,ShopifyWebhookApi,CheckoutApi,ShopifyProductWebhookApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'order_list', OrdersApi, basename='orders')





urlpatterns = [
    path('callback', OrderCallbackApi.as_view(), name='callback'),
    path('pay_webhook', ShopifyWebhookApi.as_view(), name='webhook'),
    path('product_webhook', ShopifyProductWebhookApi.as_view(), name='product_webhook'),
    path('checkout', CheckoutApi.as_view(), name='checkout'),
]
urlpatterns += router.urls
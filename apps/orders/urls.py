from django.urls import path
from .apis import OrdersApi,OrderCallbackApi,ShopifyWebhookApi,CheckoutApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'order', OrdersApi, basename='orders')





urlpatterns = [
    path('callback', OrderCallbackApi.as_view(), name='callback'),
    path('pay_webhook', ShopifyWebhookApi.as_view(), name='webhook'),
    path('checkout', CheckoutApi.as_view(), name='checkout'),
]
urlpatterns += router.urls
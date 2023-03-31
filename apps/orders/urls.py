from django.urls import path
from .apis import OrdersApi,UserOrdersApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'order', OrdersApi, basename='orders')
router.register(r'userorders',UserOrdersApi,basename="userorders")


urlpatterns = []
urlpatterns += router.urls
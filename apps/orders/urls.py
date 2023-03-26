from django.urls import path
from .apis import OrdersApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'', OrdersApi, basename='orders')


urlpatterns = []
urlpatterns += router.urls
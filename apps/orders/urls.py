from django.urls import path
from .apis import OrdersApi,UserOrdersApi
from rest_framework import routers
from .apis import EmailView,VerifyView

router = routers.DefaultRouter()
router.register(r'order', OrdersApi, basename='orders')
router.register(r'userorders',UserOrdersApi,basename="userorders")




urlpatterns = [
    path("test/", EmailView.as_view(), name="aaa"),
    path("verify/", VerifyView.as_view(), name="bbb"),
]
urlpatterns += router.urls
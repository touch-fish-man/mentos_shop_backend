from django.urls import path
from .apis import AclListApi,ProxyServerApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'acls', AclListApi)
router.register(r'', ProxyServerApi)
urlpatterns = []

urlpatterns += router.urls

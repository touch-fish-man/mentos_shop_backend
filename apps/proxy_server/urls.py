from django.urls import path
from .apis import AclsApi,ProxyServerApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'acls', AclsApi)
router.register(r'', ProxyServerApi)
urlpatterns = []

urlpatterns += router.urls

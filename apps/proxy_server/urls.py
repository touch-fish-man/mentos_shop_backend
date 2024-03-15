from django.urls import path
from .views import AclsApi,ProxyServerApi,AclGroupApi,ServerGroupApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'acls', AclsApi)
router.register(r'servers', ProxyServerApi)
router.register(r'acl-groups', AclGroupApi)
router.register(r'server-groups', ServerGroupApi)
urlpatterns = []
urlpatterns += router.urls

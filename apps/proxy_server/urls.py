from django.urls import path
from .views import AclsApi,ProxyServerApi,AclGroupApi,ServerGroupApi,CidrApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'acls', AclsApi)
router.register(r'servers', ProxyServerApi)
router.register(r'acl-groups', AclGroupApi)
router.register(r'server-groups', ServerGroupApi)
router.register(r'cidrs', CidrApi)
urlpatterns = []
urlpatterns += router.urls

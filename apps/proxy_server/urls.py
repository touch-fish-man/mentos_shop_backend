from django.urls import path
from .apis import AclListApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'acls', AclListApi)

urlpatterns = []

urlpatterns += router.urls

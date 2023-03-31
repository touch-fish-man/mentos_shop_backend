from .apis import ProductViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'products', ProductViewSet)
urlpatterns = []
urlpatterns += router.urls
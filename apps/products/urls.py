from .views import ProductViewSet,ProductCollectionViewSet,ProductTagViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'product_tags', ProductTagViewSet)
router.register(r'product_collections', ProductCollectionViewSet)
urlpatterns = []
urlpatterns += router.urls
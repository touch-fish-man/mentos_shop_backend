from django.urls import path
from apps.tickets.apis import TicksApi
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'', TicksApi, basename='tickets')

urlpatterns = [
]

urlpatterns += router.urls
from django.urls import path
from apps.tickets.apis import TicksApi, FQA
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'ticket', TicksApi, basename='tickets')
router.register(r'fqa', FQA, basename='fqa')

urlpatterns = [
]

urlpatterns += router.urls
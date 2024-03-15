from django.urls import path
from apps.tickets.views import TicketsApi, FQA
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'ticket', TicketsApi, basename='tickets')
router.register(r'fqa', FQA, basename='fqa')

urlpatterns = [
]

urlpatterns += router.urls
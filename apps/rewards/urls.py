from django.urls import path
from .apis import  CouponCodeViewSet, ExchangeRecordViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'coupon_code', CouponCodeViewSet)
router.register(r'exchange_record', ExchangeRecordViewSet)



urlpatterns = [

]
urlpatterns += router.urls
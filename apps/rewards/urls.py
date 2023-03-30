from django.urls import path
from .apis import  CouponCodeViewSet, PointRecordViewSet, GiftCardViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'coupon_code', CouponCodeViewSet)
router.register(r'point_record', PointRecordViewSet)
router.register(r'gift_card', GiftCardViewSet)



urlpatterns = [

]
urlpatterns += router.urls
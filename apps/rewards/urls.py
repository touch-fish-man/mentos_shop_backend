from django.urls import path
from .views import  CouponCodeViewSet, PointRecordViewSet, GiftCardViewSet,LevelCodeViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'coupon_code', CouponCodeViewSet)
router.register(r'point_record', PointRecordViewSet)
router.register(r'gift_card', GiftCardViewSet)
router.register(r'level_code', LevelCodeViewSet)



urlpatterns = [

]
urlpatterns += router.urls
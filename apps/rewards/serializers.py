from rest_framework import serializers
from apps.rewards.models import CouponCode, PointRecord, GiftCard


class CouponCodeSerializer(serializers.ModelSerializer):
    """
    优惠码
    """
    class Meta:
        model = CouponCode
        fields = '__all__'


class PointRecordSerializer(serializers.ModelSerializer):
    """
    兑换记录
    """
    class Meta:
        model = PointRecord
        fields = '__all__'
class GiftCardSerializer(serializers.ModelSerializer):
    """
    礼品卡
    """
    class Meta:
        model = GiftCard
        fields = '__all__'
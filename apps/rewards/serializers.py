from rest_framework import serializers
from apps.rewards.models import CouponCode, ExchangeRecord


class CouponCodeSerializer(serializers.ModelSerializer):
    """
    优惠码
    """
    class Meta:
        model = CouponCode
        fields = '__all__'


class ExchangeRecordSerializer(serializers.ModelSerializer):
    """
    兑换记录
    """
    class Meta:
        model = ExchangeRecord
        fields = '__all__'
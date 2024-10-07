from rest_framework import serializers
from .models import Payment 

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['amount', 'item', 'created_at', 'status']
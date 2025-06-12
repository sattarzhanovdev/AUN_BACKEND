from rest_framework import serializers
from .models import Transaction, Stock, SaleHistory, SaleItem

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'
        
        
class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ['code', 'name', 'price', 'quantity', 'total']

class SaleHistorySerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = SaleHistory
        fields = ['id', 'payment_type', 'total', 'date', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sale = SaleHistory.objects.create(**validated_data)
        for item in items_data:
            SaleItem.objects.create(sale=sale, **item)
        return sale

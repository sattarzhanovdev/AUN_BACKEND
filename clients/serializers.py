from rest_framework import serializers
from .models import Transaction, Stock

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class StockSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    date_added = serializers.DateField(read_only=True)  # 👈 здесь

    class Meta:
        model = Stock
        fields = ['code', 'name', 'price', 'amount', 'quantity', 'unit', 'date_added', 'price_seller']
        read_only_fields = ['quantity', 'date_added']

    def create(self, validated_data):
        validated_data['quantity'] = validated_data.pop('amount')
        return super().create(validated_data)

    def create_bulk(self, validated_data_list):
        for item in validated_data_list:
            item['quantity'] = item.pop('amount')
        return Stock.objects.bulk_create([Stock(**item) for item in validated_data_list])
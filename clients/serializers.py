from rest_framework import serializers
from .models import (
    Transaction, Stock, SaleHistory, SaleItem,
    Category, StockMovement, ReturnItem, CashSession
)


# ---------- базовые ----------------------------------------------------------

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']



class StockSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    fixed_quantity = serializers.DecimalField(
        max_digits=10, decimal_places=2
    )

    class Meta:
        model = Stock
        fields = '__all__'


class StockBulkEntrySerializer(serializers.Serializer):
    code = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True
    )
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_seller = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit = serializers.CharField()
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    fixed_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate_code(self, value):
        return [str(code) for code in value]  # Превращаем в строки, если вдруг числа

    def create(self, validated_data):
        # Мы не используем это напрямую в ViewSet
        pass


# ---------- продажи ----------------------------------------------------------

class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ['id', 'code', 'name', 'price', 'quantity', 'total']


class SaleHistorySerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = SaleHistory
        fields = ['id', 'payment_type', 'total', 'date', 'items']

    def create(self, validated_data):
        """
        - создаём саму продажу
        - создаём позиции
        - уменьшаем Stock.quantity
        - пишем StockMovement
        """
        from .models import StockMovement, Stock   # локальный импорт, чтобы избежать циклов

        items_data = validated_data.pop('items')
        sale = SaleHistory.objects.create(**validated_data)

        for item_data in items_data:
            SaleItem.objects.create(sale=sale, **item_data)

            # уменьшаем склад
            stock_obj = Stock.objects.get(code=item_data['code'])
            stock_obj.quantity -= item_data['quantity']
            stock_obj.save()

            # движение
            StockMovement.objects.create(
                stock=stock_obj,
                movement_type='sale',
                quantity=item_data['quantity'],
                sale=sale,
                comment='Продажа'
            )

        return sale


# ---------- движение по складу ----------------------------------------------

class StockMovementSerializer(serializers.ModelSerializer):
    stock_name = serializers.CharField(source='stock.name', read_only=True)

    class Meta:
        model = StockMovement
        fields = ['id', 'stock', 'stock_name', 'movement_type',
                  'quantity', 'comment', 'date', 'sale']


# ---------- возврат ----------------------------------------------------------

class ReturnItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ReturnItem
        fields = ["id", "sale_item", "quantity", "reason", "date"]
        
class CashSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CashSession
        fields = ['id', 'opened_at', 'opening_sum', 'closed_at', 'closing_sum', 'is_open']
        read_only_fields = ['opened_at', 'closed_at', 'is_open']
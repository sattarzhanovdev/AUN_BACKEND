from rest_framework import serializers
from .models import (
    Transaction, Stock, SaleHistory, SaleItem,
    Category, StockMovement, ReturnItem, CashSession, DispatchHistory, DispatchItem
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
        return [str(code) for code in value]

    def create(self, validated_data):
        codes = validated_data.pop('code')
        created = []

        for code in codes:
            stock_data = {
                **validated_data,
                'code': code,
            }

            if 'fixed_quantity' not in stock_data or stock_data['fixed_quantity'] is None:
                stock_data['fixed_quantity'] = stock_data['quantity']

            stock = Stock.objects.create(**stock_data)
            created.append(stock)

        return created  # ← здесь возвращаем список, что ок, потому что обёртка его расплющит


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
        return [str(code).strip() for code in value if code]

    def create(self, validated_data):
        codes = validated_data.pop('code')
        validated_data['code'] = ",".join(codes)

        if 'fixed_quantity' not in validated_data or validated_data['fixed_quantity'] is None:
            validated_data['fixed_quantity'] = validated_data['quantity']

        return Stock.objects.create(**validated_data)
    
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
        fields = ["id", "sale_item", "quantity", "reason", "date", "branch"]
        
class CashSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CashSession
        fields = ['id', 'opened_at', 'opening_sum', 'closed_at', 'closing_sum', 'is_open']
        read_only_fields = ['opened_at', 'closed_at', 'is_open']
        
        
class DispatchItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchItem
        exclude = ['dispatch']  # ✅ или используем fields и делаем dispatch read_only

class DispatchHistorySerializer(serializers.ModelSerializer):
    items = DispatchItemSerializer(many=True)

    class Meta:
        model = DispatchHistory
        fields = '__all__'

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        dispatch = DispatchHistory.objects.create(**validated_data)

        total = 0
        for item_data in items_data:
            item_data['dispatch'] = dispatch
            DispatchItem.objects.create(**item_data)
            total += item_data['total']

        dispatch.total = total
        dispatch.save()

        return dispatch
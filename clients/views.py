from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from django.db.models import Sum
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import get_object_or_404
from decimal import Decimal

from .models import (
    Transaction, Stock, SaleHistory, Category,
    StockMovement, ReturnItem, CashSession
)
from .serializers import (
    TransactionSerializer, StockSerializer, SaleHistorySerializer,
    CategorySerializer, StockMovementSerializer, ReturnItemSerializer, CashSessionSerializer, StockBulkEntrySerializer
)

# ------------------- ТРАНЗАКЦИИ ---------------------------------------------

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            Transaction.objects.bulk_create([Transaction(**d) for d in serializer.validated_data])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)


@api_view(['GET'])
def transaction_summary(request):
    today = now().date()
    start_of_month = today.replace(day=1)

    added_today = Transaction.objects.filter(date=today).count()
    daily_expense = Transaction.objects.filter(date=today, type='expense')\
        .aggregate(sum=Sum('amount'))['sum'] or 0
    monthly_expense = Transaction.objects.filter(date__gte=start_of_month, type='expense')\
        .aggregate(sum=Sum('amount'))['sum'] or 0

    return Response({
        "month": {"added_today": added_today},
        "daily_expense": daily_expense,
        "monthly_expense": monthly_expense
    })


# ------------------- КАТЕГОРИИ ----------------------------------------------

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# ------------------- СКЛАД ---------------------------------------------------


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer

    def create(self, request, *args, **kwargs):
        data = request.data

        # оборачиваем одиночный объект в список
        if not isinstance(data, list):
            data = [data]

        # сериализуем
        serializer = StockBulkEntrySerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)

        # сохраняем
        created_stocks = serializer.save()

        # 📌 Если вдруг что-то вернулось в виде [[obj, obj]], выравниваем
        flat_stocks = []
        for s in created_stocks:
            if isinstance(s, list):
                flat_stocks.extend(s)
            else:
                flat_stocks.append(s)

        return Response(StockSerializer(flat_stocks, many=True).data, status=status.HTTP_201_CREATED)

# ------------------- ПРОДАЖИ -------------------------------------------------

class SaleHistoryViewSet(viewsets.ModelViewSet):
    queryset = SaleHistory.objects.all().order_by('-date')
    serializer_class = SaleHistorySerializer

    # create уже реализован в сериализаторе (SaleHistorySerializer.create)
    # поэтому здесь ничего переопределять не нужно


# ------------------- ДВИЖЕНИЯ ПО СКЛАДУ (read-only) --------------------------

class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related('stock').order_by('-date')
    serializer_class = StockMovementSerializer
    
    



# ------------------- ВОЗВРАТЫ ------------------------------------------------



from rest_framework import status, viewsets
from rest_framework.response import Response
from .models import ReturnItem, Stock, StockMovement
from .serializers import ReturnItemSerializer

class ReturnItemViewSet(viewsets.ModelViewSet):
    """
    POST принимает:
      • единичный объект  {sale_item, quantity, reason?}
      • или массив таких объектов […]
    """
    queryset = ReturnItem.objects.all().order_by('-date')
    serializer_class = ReturnItemSerializer

    def create(self, request, *args, **kwargs):
        data_is_list = isinstance(request.data, list)

        serializer = self.get_serializer(
            data=request.data,
            many=data_is_list
        )
        serializer.is_valid(raise_exception=True)

        if data_is_list:
            items = [self._save_one(d) for d in serializer.validated_data]
            out = self.get_serializer(items, many=True)
        else:
            item = self._save_one(serializer.validated_data)
            out = self.get_serializer(item)

        return Response(out.data, status=status.HTTP_201_CREATED)

    def _save_one(self, data):
        """
        helper — одно возвращённое SKU
        (+ откат остатков, + StockMovement, + запись возврата)
        """
        sale_item = data["sale_item"]
        qty       = data["quantity"]
        reason    = data.get("reason", "")

        # 1. найдём товар на складе
        stock, created = Stock.objects.get_or_create(
            code=sale_item.code,
            defaults={
                "name": sale_item.name,
                "price": sale_item.price,
                "price_seller": sale_item.price,
                "quantity": 0,
                "unit": "шт"
            }
        )

        # 2. обновим остаток
        stock.quantity = (stock.quantity or Decimal("0")) + Decimal(qty)
        stock.save(update_fields=["quantity"])

        # 3. создаём движение
        StockMovement.objects.create(
            stock=stock,
            movement_type="return",
            quantity=qty,
            comment=f"Возврат по продаже #{sale_item.sale_id}"
        )

        # 4. создаём возврат
        return ReturnItem.objects.create(
            sale_item=sale_item,
            quantity=qty,
            reason=reason
        )

class CashSessionViewSet(viewsets.ModelViewSet):
    queryset = CashSession.objects.all()
    serializer_class = CashSessionSerializer

    # POST /cash-sessions/open/
    @action(detail=False, methods=['post'])
    def open(self, request):
        opening_sum = request.data.get('opening_sum', 0)
        session = CashSession(opening_sum=opening_sum)
        session.full_clean()
        session.save()
        return Response(self.get_serializer(session).data, status=status.HTTP_201_CREATED)

    # POST /cash-sessions/{id}/close/
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        session = self.get_object()
        session.close(request.data.get('closing_sum', 0))
        return Response(self.get_serializer(session).data)
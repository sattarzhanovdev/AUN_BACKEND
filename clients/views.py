from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from django.db.models import Sum
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import get_object_or_404

from .models import (
    Transaction, Stock, SaleHistory, Category,
    StockMovement, ReturnItem, CashSession
)
from .serializers import (
    TransactionSerializer, StockSerializer, SaleHistorySerializer,
    CategorySerializer, StockMovementSerializer, ReturnItemSerializer, CashSessionSerializer
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
    """
    • CRUD по складу
    • /stocks/by-code/?code=...        —  GET  поиск
    • /stocks/by-code/<code>/          —  PUT  +/- qty
    • /stocks/<id>/update-quantity/    —  PATCH точное qty
    • POST /stocks/  (list|object)     —  приход / bulk-приход
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer

    # ---------- поиск по коду ---------------------------------------------
    @action(detail=False, methods=['get'], url_path='by-code')
    def by_code(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'code is required'}, status=400)
        qs = self.queryset.filter(code=code)
        return Response(self.get_serializer(qs, many=True).data)

    # ---------- +/- qty по коду (delta) ------------------------------------
    @action(detail=False, methods=['put'], url_path='by-code/(?P<code>[^/.]+)')
    def update_quantity_by_code(self, request, code=None):
        stock = get_object_or_404(self.queryset, code=code)
        try:
            qty_delta = float(request.data.get('quantity'))
        except (TypeError, ValueError):
            return Response({'error': 'field "quantity" is required (number)'}, status=400)

        if stock.quantity + qty_delta < 0:
            return Response({'error': 'Недостаточно остатков'}, status=400)

        StockMovement.objects.create(
            stock=stock,
            movement_type='adjust',
            quantity=abs(qty_delta),
            comment='Коррекция остатка (PUT by-code)',
        )

        stock.quantity += qty_delta
        stock.save()
        return Response(self.get_serializer(stock).data)

    # ---------- PATCH /stocks/<id>/update-quantity/ (точное значение) -----
    @action(detail=True, methods=['patch'])
    def update_quantity(self, request, pk=None):
        stock = self.get_object()
        try:
            new_qty = float(request.data.get('quantity'))
        except (TypeError, ValueError):
            return Response({'error': 'quantity must be number'}, status=400)

        delta = new_qty - float(stock.quantity)
        StockMovement.objects.create(
            stock=stock,
            movement_type='adjust',
            quantity=abs(delta),
            comment='Ручная установка количества'
        )

        stock.quantity = new_qty
        stock.save()
        return Response(self.get_serializer(stock).data)

    # ---------- bulk-приход / обычный POST ---------------------------------
    def create(self, request, *args, **kwargs):
        data = request.data

        # список объектов
        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self._perform_bulk_create(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # одиночный объект
        return super().create(request, *args, **kwargs)

    # ---------- внутренний bulk-helper -------------------------------------
    def _perform_bulk_create(self, validated_list):
        """
        • если fixed_quantity не передан ‒ ставим его равным quantity
        • затем bulk_create
        """
        objs = []
        for d in validated_list:
            d['fixed_quantity'] = d.get('fixed_quantity') or d['quantity']
            objs.append(Stock(**d))

        Stock.objects.bulk_create(objs)


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
        (+ откат остатков, + StockMovement)
        """
        sale_item = data["sale_item"]
        qty = data["quantity"]
        reason = data.get("reason", "")

        # 1. вернули на склад
        try:
            stock = Stock.objects.get(code=sale_item.code)
        except Stock.DoesNotExist:
            stock = Stock.objects.create(
                code=sale_item.code,
                name=sale_item.name,
                quantity=0,
                price=sale_item.price,
                unit='шт'
            )

        stock.quantity += qty
        stock.save(update_fields=["quantity"])

        # 2. движение
        StockMovement.objects.create(
            stock=stock,
            movement_type="return",
            quantity=qty,
            comment=f"Возврат по продаже #{sale_item.sale_id}"
        )

        # 3. создаём ReturnItem
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
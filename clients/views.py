from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import get_object_or_404

from .models import Transaction
from .serializers import TransactionSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import timedelta
from .models import Transaction, Stock, SaleHistory, SaleItem
from .serializers import TransactionSerializer, StockSerializer, SaleHistorySerializer, SaleItemSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        data = request.data

        # если массив — создаём bulk
        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_bulk_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # иначе — обычный объект
        return super().create(request, *args, **kwargs)

    def perform_bulk_create(self, serializer):
        Transaction.objects.bulk_create([
            Transaction(**item) for item in serializer.validated_data
        ])


@api_view(['GET'])
def transaction_summary(request):
    today = now().date()
    start_of_month = today.replace(day=1)

    # Кол-во доходов и расходов сегодня
    added_today = Transaction.objects.filter(date=today).count()

    # Сумма расходов за сегодня
    daily_expense = Transaction.objects.filter(date=today, type='expense')\
        .aggregate(sum=models.Sum('amount'))['sum'] or 0

    # Сумма расходов за месяц
    monthly_expense = Transaction.objects.filter(date__gte=start_of_month, type='expense')\
        .aggregate(sum=models.Sum('amount'))['sum'] or 0

    return Response({
        "month": {
            "added_today": added_today
        },
        "daily_expense": daily_expense,
        "monthly_expense": monthly_expense
    })



class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer

    @action(detail=False, methods=['get'], url_path='by-code')
    def get_by_code(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'code is required'}, status=status.HTTP_400_BAD_REQUEST)

        items = Stock.objects.filter(code=code)
        if not items.exists():
            return Response([], status=status.HTTP_200_OK)

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['put'], url_path='by-code/(?P<code>[^/.]+)')
    def subtract_quantity_by_code(self, request, code=None):
        try:
            stock = Stock.objects.get(code=code)
        except Stock.DoesNotExist:
            return Response({'error': 'Товар не найден'}, status=404)

        try:
            subtract_value = float(request.data.get('quantity', 0))
        except (ValueError, TypeError):
            return Response({'error': 'Некорректное значение quantity'}, status=400)

        if subtract_value < 0:
            return Response({'error': 'Количество не может быть отрицательным'}, status=400)

        if stock.quantity < subtract_value:
            return Response({'error': 'Недостаточно товара на складе'}, status=400)

        stock.quantity -= subtract_value
        stock.save()

        serializer = self.get_serializer(stock)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data

        # если массив
        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)

            # сохраняем каждую запись
            created = [self.get_serializer().create(item) for item in serializer.validated_data]

            return Response(self.get_serializer(created, many=True).data, status=status.HTTP_201_CREATED)

        # если объект
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)
    
class SaleHistoryViewSet(viewsets.ModelViewSet):
    queryset = SaleHistory.objects.all().order_by('-date')
    serializer_class = SaleHistorySerializer

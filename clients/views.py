from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.utils.timezone import now
from datetime import timedelta

from .models import Transaction
from .serializers import TransactionSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import timedelta
from .models import Transaction, Stock
from .serializers import TransactionSerializer, StockSerializer

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

    def create(self, request, *args, **kwargs):
        data = request.data

        # если массив
        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)

            # ✅ вызываем create_bulk вручную на классе сериализатора
            created = StockSerializer().create_bulk(serializer.validated_data)

            return Response(StockSerializer(created, many=True).data, status=status.HTTP_201_CREATED)

        # если объект
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)
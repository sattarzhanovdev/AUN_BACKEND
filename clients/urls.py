from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, transaction_summary, StockViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'stocks', StockViewSet, basename='stock')

urlpatterns = [
    path('', include(router.urls)),
    path('transactions/summary/', transaction_summary),    
]


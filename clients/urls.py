from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, transaction_summary, StockViewSet, SaleHistoryViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'stocks', StockViewSet, basename='stock')
router.register(r'sales', SaleHistoryViewSet, basename='sales')


urlpatterns = [
    path('', include(router.urls)),
    path('transactions/summary/', transaction_summary),    
]


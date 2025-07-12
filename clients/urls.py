from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransactionViewSet, transaction_summary,
    StockViewSet, SaleHistoryViewSet,
    CategoryViewSet, StockMovementViewSet,
    ReturnItemViewSet, CashSessionViewSet, DispatchHistoryViewSet
)

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'stocks', StockViewSet, basename='stock')
router.register(r'sales', SaleHistoryViewSet, basename='sale')
router.register(r'stock-movements', StockMovementViewSet, basename='movement')
router.register(r'returns', ReturnItemViewSet, basename='return')
router.register(r'cash-sessions', CashSessionViewSet, basename='cashsession')
router.register(r'dispatches', DispatchHistoryViewSet, basename='dispatch')


urlpatterns = [
    path('', include(router.urls)),
    path('transactions/summary/', transaction_summary),
]

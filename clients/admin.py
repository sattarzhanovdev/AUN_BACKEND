from django.contrib import admin
from .models import (
    Transaction, Stock, SaleHistory, SaleItem,
    Category, StockMovement, ReturnItem, CashSession
)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['type', 'name', 'amount', 'date']
    list_filter = ['type', 'date']
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display     = ('code', 'name', 'quantity', 'fixed_quantity', 'unit', 'category', 'fixed_quantity')


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['code', 'name', 'price', 'quantity', 'total']


@admin.register(SaleHistory)
class SaleHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment_type', 'total', 'date']
    list_filter = ['payment_type', 'date']
    inlines = [SaleItemInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['stock', 'movement_type', 'quantity', 'comment', 'date']
    list_filter = ['movement_type', 'date']
    search_fields = ['stock__name', 'comment']


@admin.register(ReturnItem)
class ReturnItemAdmin(admin.ModelAdmin):
    list_display = ['sale_item', 'quantity', 'reason', 'date']
    list_filter = ['date']
    search_fields = ['sale_item__name', 'reason']

@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display  = ('opened_at', 'closed_at', 'opening_sum', 'closing_sum', 'is_open')
    list_filter   = ('closed_at',)
    readonly_fields = ('opened_at', 'closed_at')
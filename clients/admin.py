from django.contrib import admin
from .models import Transaction, Stock

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'name', 'amount', 'date')
    list_filter = ('type', 'date')
    search_fields = ('name',)
    ordering = ('-date',)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'quantity', 'price', 'date_added')
    search_fields = ('code', 'name')
    list_filter = ('date_added',)
from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'name', 'amount', 'date')
    list_filter = ('type', 'date')
    search_fields = ('name',)
    ordering = ('-date',)

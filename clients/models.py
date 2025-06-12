from django.db import models
from django.utils.timezone import now
from decimal import Decimal
from django.core.validators import MinValueValidator

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]

    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    date = models.DateField(default=now)

    def __str__(self):
        return f"{self.get_type_display()} — {self.name}: {self.amount}"



class Stock(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_seller = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)
    date_added = models.DateField(default=now)

    def __str__(self):
        return f"{self.code} — {self.name}"
    
class SaleHistory(models.Model):
    payment_type = models.CharField(
        max_length=50,
        choices=[('cash', 'Наличные'), ('card', 'Карта')],
        verbose_name="Тип оплаты"
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итого")
    date = models.DateTimeField(default=now, verbose_name="Дата продажи")

    def __str__(self):
        return f"Продажа на {self.total} сом — {self.date.strftime('%d.%m.%Y %H:%M')}"

    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"

class SaleItem(models.Model):
    sale = models.ForeignKey(SaleHistory, related_name="items", on_delete=models.CASCADE)
    code = models.CharField(max_length=100, verbose_name="Код товара")
    name = models.CharField(max_length=255, verbose_name="Наименование")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")

    def __str__(self):
        return f"{self.name} x{self.quantity}"

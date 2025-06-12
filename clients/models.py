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
    code = models.CharField(max_length=50, unique=True, verbose_name="Код товара")
    name = models.CharField(max_length=255, verbose_name="Наименование")
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Количество"
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Цена за единицу"
    )
    price_seller = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Цена поставщика"
    )
    unit = models.CharField(max_length=50, default='шт.', verbose_name="Единица измерения")
    date_added = models.DateField(default=now, verbose_name="Дата добавления")

    def __str__(self):
        return f"{self.code} — {self.name}"

    class Meta:
        verbose_name = "Товар на складе"
        verbose_name_plural = "Склад"
from django.db import models
from django.utils.timezone import now
from decimal import Decimal
from django.core.validators import MinValueValidator
# models.py
from django.db import models, transaction
from django.db.models import F
from django.utils.timezone import now


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


class Category(models.Model):
    """Категория товара"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Stock(models.Model):
    code          = models.CharField(max_length=50, unique=True)
    name          = models.CharField(max_length=255)
    price         = models.DecimalField(max_digits=10, decimal_places=2)
    price_seller  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity      = models.DecimalField(max_digits=10, decimal_places=2)
    fixed_quantity= models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,          # 👈 скрыто в админ-форме
        null=True,
        verbose_name="Получено изначально"
    )
    unit          = models.CharField(max_length=50)
    date_added    = models.DateField(default=now)

    category      = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stocks',
        verbose_name="Категория"
    )

    # --- магия сохранения
    def save(self, *args, **kwargs):
        # при первом сохранении (создание) — зафиксировать стартовый остаток
        if self.pk is None:
            self.fixed_quantity = self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} — {self.name}"

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Товары на складе"


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


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', 'Приход'),
        ('sale', 'Продажа'),
        ('return', 'Возврат'),
        ('adjust', 'Коррекция'),
    ]

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    comment = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateTimeField(default=now)

    sale = models.ForeignKey(
        SaleHistory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} {self.stock.unit} — {self.stock.name}"

    class Meta:
        verbose_name = "Движение по складу"
        verbose_name_plural = "Движения по складу"



class ReturnItem(models.Model):
    # ⬇️ было OneToOneField → меняем на ForeignKey
    sale_item = models.ForeignKey(
        'SaleItem',
        on_delete=models.CASCADE,
        related_name='return_records'
    )
    quantity = models.PositiveIntegerField()
    reason   = models.CharField(max_length=255, blank=True, null=True)
    date     = models.DateTimeField(default=now)

    def __str__(self):
        return f"Возврат {self.quantity} × {self.sale_item.name}"

    class Meta:
        verbose_name = "Возврат позиции"
        verbose_name_plural = "Возвраты позиций"
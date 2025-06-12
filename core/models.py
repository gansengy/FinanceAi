from django.db import models
from django.utils.timezone import now


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Назва категорії")
    icon = models.CharField(max_length=10, default="📦", verbose_name="Іконка")
    is_default = models.BooleanField(default=False, verbose_name="Базова категорія")
    is_income = models.BooleanField(default=False, verbose_name="Категорія прибутку")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ['name']

    def __str__(self):
        return f"{self.icon} {self.name}"

    def delete(self, *args, **kwargs):
        if self.is_default:
            raise models.ProtectedError(
                "Не можна видалити базову категорію",
                self
            )
        super().delete(*args, **kwargs)


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('expense', 'Витрата'),
        ('income', 'Прибуток'),
    ]

    name = models.CharField(max_length=255, verbose_name="Назва")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сума")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категорія")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='expense', verbose_name="Тип")
    created_at = models.DateTimeField(default=now, verbose_name="Створено")  # Змінено з auto_now_add на default

    class Meta:
        verbose_name = "Транзакція"
        verbose_name_plural = "Транзакції"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.price} грн ({self.get_transaction_type_display()})"

    def __getitem__(self, key):
        """Allow bracket notation access to model fields"""
        return getattr(self, key)
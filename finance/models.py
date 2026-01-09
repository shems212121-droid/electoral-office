from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="القسم / الجهة")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "قسم مالي"
        verbose_name_plural = "الأقسام المالية"

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'قبض (استلام)'),
        ('expense', 'صرف'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions', verbose_name="الجهة")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="نوع العملية")
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="المبلغ (د.ع)")
    description = models.TextField(verbose_name="التفاصيل")
    date = models.DateField(default=timezone.now, verbose_name="التاريخ")
    receipt_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="رقم الوصل")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "حركة مالية"
        verbose_name_plural = "الحركات المالية"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} - {self.category.name}"

from django.contrib import admin
from .models import Category, Transaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'category', 'amount', 'date', 'receipt_number')
    list_filter = ('transaction_type', 'category', 'date')
    search_fields = ('description', 'receipt_number')
    date_hierarchy = 'date'

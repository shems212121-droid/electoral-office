from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['category', 'transaction_type', 'amount', 'date', 'description', 'receipt_number']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

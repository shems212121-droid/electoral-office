from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib import messages
from .models import Transaction, Category
from .forms import TransactionForm

@login_required
def finance_dashboard(request):
    # Summary Cards
    total_income = Transaction.objects.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Transaction.objects.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense

    # Recent Transactions
    recent_transactions = Transaction.objects.select_related('category').all()[:10]

    # Category Breakdown
    categories = Category.objects.all()
    category_data = []
    
    for cat in categories:
        inc = cat.transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        exp = cat.transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        category_data.append({
            'name': cat.name,
            'income': inc,
            'expense': exp,
            'balance': inc - exp
        })

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'recent_transactions': recent_transactions,
        'category_data': category_data
    }
    return render(request, 'finance/dashboard.html', context)

@login_required
def transaction_list(request):
    transactions = Transaction.objects.select_related('category').all()
    
    # Simple filtering
    t_type = request.GET.get('type')
    if t_type:
        transactions = transactions.filter(transaction_type=t_type)
        
    context = {
        'transactions': transactions
    }
    return render(request, 'finance/transaction_list.html', context)

@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الحركة المالية بنجاح')
            return redirect('finance_dashboard')
    else:
        form = TransactionForm()
    
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'إضافة حركة مالية'})

@login_required
def transaction_update(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل الحركة المالية بنجاح')
            return redirect('finance_dashboard')
    else:
        form = TransactionForm(instance=transaction)
    
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'تعديل حركة مالية'})

@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'تم حذف الحركة المالية بنجاح')
        return redirect('finance_dashboard')
    return render(request, 'finance/transaction_confirm_delete.html', {'transaction': transaction})

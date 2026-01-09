from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import date
from .models import CampaignTask


@login_required
def get_overdue_tasks(request):
    """API للحصول على المهام المتأخرة"""
    # الحصول على المهام المتأخرة غير المكتملة
    overdue_tasks = []
    
    tasks = CampaignTask.objects.filter(
        status__in=['pending', 'in_progress']
    ).exclude(due_date__isnull=True)
    
    for task in tasks:
        if task.is_overdue():
            overdue_tasks.append({
                'id': task.id,
                'title': task.title,
                'due_date': task.due_date.strftime('%Y-%m-%d'),
                'days_overdue': task.days_overdue(),
                'priority': task.get_priority_display(),
                'assigned_to': task.assigned_to,
                'status': task.get_status_display(),
            })
    
    return JsonResponse({
        'count': len(overdue_tasks),
        'tasks': overdue_tasks
    })

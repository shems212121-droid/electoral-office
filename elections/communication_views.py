from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from .models import (
    Voter, ElectoralPublic, PersonalVoterRecord, CandidateMonitor, 
    PoliticalEntityAgent, CenterDirector, CommunicationLog
)
from .forms import CommunicationLogForm

@login_required
def communications_dashboard(request):
    """لوحة تحكم الاتصالات الموحدة"""
    # آخر 50 اتصال
    recent_logs = CommunicationLog.objects.select_related('caller').order_by('-created_at')[:50]
    
    # إحصائيات سريعة لليوم
    from django.utils import timezone
    today = timezone.now().date()
    today_count = CommunicationLog.objects.filter(created_at__date=today).count()
    my_calls_count = CommunicationLog.objects.filter(created_at__date=today, caller=request.user).count()
    
    context = {
        'recent_logs': recent_logs,
        'today_count': today_count,
        'my_calls_count': my_calls_count,
        'form': CommunicationLogForm(), # نموذج فارغ للاستخدام في الـ Modal
    }
    return render(request, 'elections/communications/dashboard.html', context)

@login_required
def search_contacts(request):
    """بحث شامل عن جهات الاتصال في جميع الجداول"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    # دالة مساعدة لإضافة النتائج
    def add_results(queryset, type_label, model_name, info_field=None):
        count = 0
        for item in queryset:
            if count >= 5: break # Max 5 per category
            
            phone = getattr(item, 'phone', None) or getattr(item, 'phone_number', '')
            
            info = ""
            if info_field and hasattr(item, info_field):
                info = str(getattr(item, info_field))
            elif hasattr(item, 'voter_number'):
                info = f"رقم الناخب: {item.voter_number}"
            elif hasattr(item, 'registration_center_name'):
                info = item.registration_center_name
                
            results.append({
                'id': item.id,
                'name': item.full_name,
                'type': type_label,
                'phone': phone,
                'model': model_name,
                'info': info
            })
            count += 1

    # 1. المرتكزات (Anchors / ElectoralPublic)
    anchors = ElectoralPublic.objects.filter(
        Q(full_name__icontains=query) | Q(voter_number__icontains=query) | Q(phone_number__icontains=query)
    )
    add_results(anchors, 'مرتكز', 'electoralpublic', 'registration_center_name')

    # 2. المعرفين (Introducers / PersonalVoterRecord)
    introducers = PersonalVoterRecord.objects.filter(
        Q(full_name__icontains=query) | Q(voter_number__icontains=query) | Q(phone_number__icontains=query)
    )
    add_results(introducers, 'معرف', 'personalvoterrecord', 'registration_center_name')

    # 3. المراقبين (CandidateMonitor)
    monitors = CandidateMonitor.objects.filter(
        Q(full_name__icontains=query) | Q(voter_number__icontains=query) | Q(phone__icontains=query)
    )
    add_results(monitors, 'مراقب', 'candidatemonitor', 'voting_center_name')

    # 4. الوكلاء (PoliticalEntityAgent)
    agents = PoliticalEntityAgent.objects.filter(
        Q(full_name__icontains=query) | Q(voter_number__icontains=query) | Q(phone__icontains=query)
    )
    add_results(agents, 'وكيل', 'politicalentityagent', 'assigned_center_name')

    # 5. مدراء المراكز (CenterDirector)
    directors = CenterDirector.objects.filter(
        Q(full_name__icontains=query) | Q(phone_number__icontains=query)
    )
    add_results(directors, 'مدير مركز', 'centerdirector', 'assigned_center_name')

    # 6. الناخبين (Voters) - نضعهم في النهاية لكثرتهم
    voters = Voter.objects.filter(
        Q(full_name__icontains=query) | Q(voter_number__icontains=query) | Q(phone__icontains=query)
    )
    add_results(voters, 'ناخب', 'voter', 'governorate')
    
    return JsonResponse({'results': results})

@login_required
def log_call(request):
    """تسجيل نتيجة الاتصال"""
    if request.method == 'POST':
        import json
        
        # دعم JSON أو Form Data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        model_name = data.get('model_name')
        object_id = data.get('object_id')
        phone_number = data.get('phone_number')
        call_status = data.get('call_status')
        outcome = data.get('outcome')

        if not all([model_name, object_id, call_status]):
            return JsonResponse({'status': 'error', 'message': 'البيانات ناقصة'})

        # تحديد الـ Model Class
        model_map = {
            'voter': Voter,
            'electoralpublic': ElectoralPublic,
            'personalvoterrecord': PersonalVoterRecord,
            'candidatemonitor': CandidateMonitor,
            'politicalentityagent': PoliticalEntityAgent,
            'centerdirector': CenterDirector
        }
        
        model_class = model_map.get(model_name.lower())
        if not model_class:
            return JsonResponse({'status': 'error', 'message': 'نوع السجل غير معروف'})
            
        try:
            content_type = ContentType.objects.get_for_model(model_class)
            
            CommunicationLog.objects.create(
                caller=request.user,
                content_type=content_type,
                object_id=object_id,
                phone_number=phone_number,
                call_status=call_status,
                outcome=outcome
            )
            
            return JsonResponse({'status': 'success', 'message': 'تم حفظ المكالمة بنجاح'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'طريقة غير مسموح بها'})

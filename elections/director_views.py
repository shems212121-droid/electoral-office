# -*- coding: utf-8 -*-
"""
Views خاصة بمدراء المراكز الانتخابية
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Q

from elections.models import (
    CenterDirector, PoliticalEntityAgent, CandidateMonitor,
    AttendanceRecord, DirectorLoginLog
)


def director_required(view_func):
    """Decorator للتحقق من أن المستخدم هو مدير مركز"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        try:
            director = CenterDirector.objects.get(user=request.user)
            request.director = director
            return view_func(request, *args, **kwargs)
        except CenterDirector.DoesNotExist:
            messages.error(request, 'هذه الصفحة مخصصة لمدراء المراكز فقط')
            return redirect('dashboard')
    
    return wrapper


@login_required
@director_required
def director_dashboard(request):
    """لوحة تحكم مدير المركز"""
    director = request.director
    
    # إحصائيات الوكلاء في المركز
    agents = PoliticalEntityAgent.objects.filter(
        assigned_center_number=director.assigned_center_number
    )
    agents_count = agents.count()
    
    # إحصائيات المراقبين في المركز
    monitors = CandidateMonitor.objects.filter(
        voting_center_number=director.assigned_center_number
    )
    monitors_count = monitors.count()
    
    # سجلات الحضور اليوم
    today = timezone.now().date()
    today_attendance = AttendanceRecord.objects.filter(
        recorded_by=director,
        created_at__date=today
    ).select_related('agent', 'monitor')
    
    # عدد الحاضرين حالياً (دخلوا ولم يخرجوا)
    present_now = AttendanceRecord.objects.filter(
        recorded_by=director,
        status='checked_in',
        check_out_time__isnull=True
    ).count()
    
    # آخر 10 سجلات حضور
    recent_attendance = AttendanceRecord.objects.filter(
        recorded_by=director
    ).select_related('agent', 'monitor').order_by('-created_at')[:10]
    
    context = {
        'director': director,
        'agents_count': agents_count,
        'monitors_count': monitors_count,
        'today_attendance_count': today_attendance.count(),
        'present_now': present_now,
        'recent_attendance': recent_attendance,
        'page_title': f'لوحة تحكم مدير المركز - {director.assigned_center_number}',
    }
    
    return render(request, 'elections/director/dashboard.html', context)


@login_required
@director_required
def director_agents_list(request):
    """قائمة الوكلاء في مركز المدير"""
    director = request.director
    
    # جميع الوكلاء في المركز
    agents = PoliticalEntityAgent.objects.filter(
        assigned_center_number=director.assigned_center_number
    ).select_related('political_entity').order_by('full_name')
    
    # إضافة حالة الحضور لكل وكيل
    for agent in agents:
        # آخر سجل حضور
        last_record = AttendanceRecord.objects.filter(
            agent=agent,
            recorded_by=director
        ).order_by('-created_at').first()
        
        if last_record:
            agent.last_attendance = last_record
            # هل حاضر حالياً؟
            agent.is_present = (
                last_record.status == 'checked_in' and 
                last_record.check_out_time is None
            )
        else:
            agent.last_attendance = None
            agent.is_present = False
    
    context = {
        'director': director,
        'agents': agents,
        'page_title': f'وكلاء المركز {director.assigned_center_number}',
    }
    
    return render(request, 'elections/director/agents_list.html', context)


@login_required
@director_required
def director_monitors_list(request):
    """قائمة المراقبين في مركز المدير"""
    director = request.director
    
    # جميع المراقبين في المركز
    monitors = CandidateMonitor.objects.filter(
        voting_center_number=director.assigned_center_number
    ).select_related('candidate').order_by('full_name')
    
    # إضافة حالة الحضور لكل مراقب
    for monitor in monitors:
        # آخر سجل حضور
        last_record = AttendanceRecord.objects.filter(
            monitor=monitor,
            recorded_by=director
        ).order_by('-created_at').first()
        
        if last_record:
            monitor.last_attendance = last_record
            monitor.is_present = (
                last_record.status == 'checked_in' and 
                last_record.check_out_time is None
            )
        else:
            monitor.last_attendance = None
            monitor.is_present = False
    
    context = {
        'director': director,
        'monitors': monitors,
        'page_title': f'مراقبو المركز {director.assigned_center_number}',
    }
    
    return render(request, 'elections/director/monitors_list.html', context)


@login_required
@director_required
def record_attendance(request, person_type, person_id, action):
    """تسجيل حضور أو انصراف"""
    director = request.director
    
    try:
        if person_type == 'agent':
            person = get_object_or_404(
                PoliticalEntityAgent, 
                id=person_id,
                assigned_center_number=director.assigned_center_number
            )
            record_type = 'agent'
        elif person_type == 'monitor':
            person = get_object_or_404(
                CandidateMonitor,
                id=person_id,
                voting_center_number=director.assigned_center_number
            )
            record_type = 'monitor'
        else:
            messages.error(request, 'نوع غير صحيح')
            return redirect('director_dashboard')
        
        if action == 'check_in':
            # تسجيل حضور
            AttendanceRecord.objects.create(
                agent=person if person_type == 'agent' else None,
                monitor=person if person_type == 'monitor' else None,
                recorded_by=director,
                record_type=record_type,
                status='checked_in',
                check_in_time=timezone.now()
            )
            messages.success(request, f'✅ تم تسجيل حضور {person.full_name}')
            
        elif action == 'check_out':
            # البحث عن آخر سجل حضور بدون انصراف
            if person_type == 'agent':
                last_record = AttendanceRecord.objects.filter(
                    agent=person,
                    recorded_by=director,
                    check_out_time__isnull=True
                ).order_by('-check_in_time').first()
            else:
                last_record = AttendanceRecord.objects.filter(
                    monitor=person,
                    recorded_by=director,
                    check_out_time__isnull=True
                ).order_by('-check_in_time').first()
            
            if last_record:
                last_record.status = 'checked_out'
                last_record.check_out_time = timezone.now()
                last_record.save()
                
                duration = last_record.get_duration()
                messages.success(request, f'✅ تم تسجيل انصراف {person.full_name} (المدة: {duration})')
            else:
                messages.warning(request, f'⚠️ لا يوجد سجل حضور لـ {person.full_name}')
        
        # العودة للصفحة المناسبة
        if person_type == 'agent':
            return redirect('director_agents_list')
        else:
            return redirect('director_monitors_list')
            
    except Exception as e:
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('director_dashboard')


@login_required
@director_required  
def attendance_history(request):
    """سجل الحضور والانصراف الكامل"""
    director = request.director
    
    # تصفية حسب التاريخ
    date_filter = request.GET.get('date')
    records = AttendanceRecord.objects.filter(
        recorded_by=director
    ).select_related('agent', 'monitor')
    
    if date_filter:
        records = records.filter(created_at__date=date_filter)
    
    records = records.order_by('-created_at')
    
    context = {
        'director': director,
        'records': records,
        'date_filter': date_filter,
        'page_title': 'سجل الحضور والانصراف',
    }
    
    return render(request, 'elections/director/attendance_history.html', context)


@login_required
@director_required
def director_logout(request):
    """تسجيل خروج مدير المركز"""
    director = request.director
    
    # تسجيل وقت الخروج في آخر سجل دخول
    last_login = DirectorLoginLog.objects.filter(
        director=director,
        user=request.user,
        logout_time__isnull=True
    ).order_by('-login_time').first()
    
    if last_login:
        last_login.logout_time = timezone.now()
        last_login.save()
    
    from django.contrib.auth import logout
    logout(request)
    
    messages.success(request, 'تم تسجيل الخروج بنجاح')
    return redirect('login')

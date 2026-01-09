from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import CenterDirector, PoliticalEntityAgent, Organization
from .center_forms import CenterDirectorForm, PoliticalEntityAgentForm


# ==================== Center Directors Views ====================

@login_required
def center_director_list(request):
    """قائمة مدراء المراكز الانتخابية"""
    voting_type = request.GET.get('voting_type', '')
    status = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    directors = CenterDirector.objects.all()
    
    # Filters
    if voting_type:
        directors = directors.filter(voting_type=voting_type)
    if status:
        directors = directors.filter(status=status)
    if search_query:
        directors = directors.filter(
            Q(full_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(assigned_center_number__icontains=search_query) |
            Q(assigned_center_name__icontains=search_query)
        )
    
    # Annotate with agent counts
    directors = directors.annotate(
        agents_count=Count('agents')
    ).order_by('voting_type', 'assigned_center_number')
    
    # Statistics
    total_general = CenterDirector.objects.filter(voting_type='general').count()
    total_special = CenterDirector.objects.filter(voting_type='special').count()
    active_directors = CenterDirector.objects.filter(status='active').count()
    
    context = {
        'directors': directors,
        'total_general': total_general,
        'total_special': total_special,
        'active_directors': active_directors,
        'voting_type_filter': voting_type,
        'status_filter': status,
        'search_query': search_query,
    }
    
    return render(request, 'elections/center_directors/list.html', context)


@login_required
def center_director_add(request):
    """إضافة مدير مركز جديد"""
    if request.method == 'POST':
        form = CenterDirectorForm(request.POST)
        if form.is_valid():
            try:
                director = form.save(commit=False)
                director.added_by = request.user
                
                # إنشاء حساب مستخدم تلقائياً
                from django.contrib.auth.models import User
                import random
                import string
                
                # اسم المستخدم: director_[رقم المركز]
                username = f"director_{director.assigned_center_number}".replace('-', '_')
                
                # كلمة مرور عشوائية (8 أحرف وأرقام)
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # التحقق من عدم وجود المستخدم مسبقاً
                if User.objects.filter(username=username).exists():
                    # إضافة رقم عشوائي للاسم
                    username = f"{username}_{random.randint(100, 999)}"
                
                # إنشاء المستخدم
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=director.full_name,
                    email=director.email if director.email else '',
                    is_staff=False,  # ليس admin
                    is_active=True
                )
                
                # ربط المستخدم بالمدير
                director.user = user
                director.save()
                
                # عرض رسالة النجاح مع بيانات تسجيل الدخول
                success_message = f'''
                ✅ تم إضافة مدير المركز {director.full_name} بنجاح!
                
                📋 بيانات تسجيل الدخول:
                👤 اسم المستخدم: {username}
                🔑 كلمة المرور: {password}
                
                ⚠️ يرجى حفظ هذه المعلومات وتسليمها للمدير
                (لن يمكن عرض كلمة المرور مرة أخرى)
                '''
                messages.success(request, success_message)
                
                return redirect('center_director_detail', pk=director.pk)
                
            except Exception as e:
                from django.db import IntegrityError
                if isinstance(e, IntegrityError):
                    if 'phone' in str(e):
                        form.add_error('phone', 'رقم الهاتف مسجل مسبقاً. يرجى استخدام رقم هاتف آخر.')
                    elif 'assigned_center_number' in str(e):
                        form.add_error('assigned_center_number', 'رقم المركز مسجل مسبقاً. يجب أن يكون لكل مركز مدير واحد فقط.')
                    else:
                        messages.error(request, f'خطأ في قاعدة البيانات: {str(e)}')
                else:
                    messages.error(request, f'حدث خطأ أثناء الحفظ: {str(e)}')
                # إعادة عرض النموذج مع الأخطاء
        else:
            # عرض رسالة خطأ عامة مع تفاصيل الأخطاء
            error_messages = []
            for field, errors in form.errors.items():
                if field == '__all__':
                    error_messages.extend(errors)
                else:
                    field_label = form.fields.get(field).label if field in form.fields else field
                    for error in errors:
                        error_messages.append(f'{field_label}: {error}')
            
            if error_messages:
                messages.error(request, 'يوجد أخطاء في النموذج: ' + ' | '.join(error_messages))
    else:
        form = CenterDirectorForm()
    
    context = {
        'form': form,
        'page_title': 'إضافة مدير مركز انتخابي',
    }
    return render(request, 'elections/center_directors/form.html', context)


@login_required
def center_director_edit(request, pk):
    """تعديل مدير مركز"""
    director = get_object_or_404(CenterDirector, pk=pk)
    
    if request.method == 'POST':
        form = CenterDirectorForm(request.POST, instance=director)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'تم تحديث بيانات {director.full_name} بنجاح')
                return redirect('center_director_detail', pk=director.pk)
            except Exception as e:
                from django.db import IntegrityError
                if isinstance(e, IntegrityError):
                    if 'phone' in str(e):
                        form.add_error('phone', 'رقم الهاتف مسجل مسبقاً. يرجى استخدام رقم هاتف آخر.')
                    elif 'assigned_center_number' in str(e):
                        form.add_error('assigned_center_number', 'رقم المركز مسجل مسبقاً. يجب أن يكون لكل مركز مدير واحد فقط.')
                    else:
                        messages.error(request, f'خطأ في قاعدة البيانات: {str(e)}')
                else:
                    messages.error(request, f'حدث خطأ أثناء الحفظ: {str(e)}')
        else:
            # عرض رسالة خطأ عامة مع تفاصيل الأخطاء
            error_messages = []
            for field, errors in form.errors.items():
                if field == '__all__':
                    error_messages.extend(errors)
                else:
                    field_label = form.fields.get(field).label if field in form.fields else field
                    for error in errors:
                        error_messages.append(f'{field_label}: {error}')
            
            if error_messages:
                messages.error(request, 'يوجد أخطاء في النموذج: ' + ' | '.join(error_messages))
    else:
        form = CenterDirectorForm(instance=director)
    
    context = {
        'form': form,
        'director': director,
        'page_title': f'تعديل مدير المركز - {director.full_name}',
    }
    return render(request, 'elections/center_directors/form.html', context)


@login_required
def center_director_detail(request, pk):
    """عرض تفاصيل مدير المركز"""
    director = get_object_or_404(CenterDirector, pk=pk)
    
    # Get agents under this director
    agents = director.agents.select_related('political_entity').order_by('assigned_station_number')
    
    # Agent statistics
    total_agents = agents.count()
    registered_agents = agents.filter(status='registered').count()
    approved_agents = agents.filter(status='approved').count()
    badge_issued_agents = agents.filter(status='badge_issued').count()
    
    # Stations coverage
    stations = agents.values('assigned_station_number').distinct().count()
    
    context = {
        'director': director,
        'agents': agents,
        'total_agents': total_agents,
        'registered_agents': registered_agents,
        'approved_agents': approved_agents,
        'badge_issued_agents': badge_issued_agents,
        'stations_covered': stations,
    }
    
    return render(request, 'elections/center_directors/detail.html', context)


@login_required
def center_director_delete(request, pk):
    """حذف مدير مركز"""
    if request.method == 'POST':
        director = get_object_or_404(CenterDirector, pk=pk)
        name = director.full_name
        try:
            # التحقق من وجود وكلاء مرتبطين
            agents_count = director.agents.count()
            
            if agents_count > 0:
                messages.error(request, f'لا يمكن حذف مدير المركز {name} لأنه يحتوي على {agents_count} وكيل(لاء) مرتبطين')
                return redirect('center_director_detail', pk=pk)
            
            director.delete()
            messages.success(request, f'تم حذف مدير المركز {name} بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء الحذف: {str(e)}')
            return redirect('center_director_detail', pk=pk)
    
    return redirect('center_director_list')


# ==================== Political Entity Agents Views ====================

@login_required
def political_entity_agent_list(request):
    """قائمة وكلاء الكيانات السياسية"""
    entity_id = request.GET.get('entity', '')
    director_id = request.GET.get('director', '')
    status = request.GET.get('status', '')
    center_number = request.GET.get('center', '')
    search_query = request.GET.get('search', '')
    
    agents = PoliticalEntityAgent.objects.select_related('political_entity', 'center_director')
    
    # Filters
    if entity_id:
        agents = agents.filter(political_entity_id=entity_id)
    if director_id:
        agents = agents.filter(center_director_id=director_id)
    if status:
        agents = agents.filter(status=status)
    if center_number:
        agents = agents.filter(assigned_center_number=center_number)
    if search_query:
        agents = agents.filter(
            Q(full_name__icontains=search_query) |
            Q(voter_number__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(assigned_center_number__icontains=search_query) |
            Q(assigned_station_number__icontains=search_query)
        )
    
    agents = agents.order_by('assigned_center_number', 'assigned_station_number')
    
    # Statistics
    total_agents = PoliticalEntityAgent.objects.count()
    registered = PoliticalEntityAgent.objects.filter(status='registered').count()
    approved = PoliticalEntityAgent.objects.filter(status='approved').count()
    badge_issued = PoliticalEntityAgent.objects.filter(status='badge_issued').count()
    
    # Get all entities and directors for filters
    entities = Organization.objects.filter(type='political_entity')
    directors = CenterDirector.objects.filter(status='active')
    
    context = {
        'agents': agents,
        'total_agents': total_agents,
        'registered': registered,
        'approved': approved,
        'badge_issued': badge_issued,
        'entities': entities,
        'directors': directors,
        'entity_filter': entity_id,
        'director_filter': director_id,
        'status_filter': status,
        'center_filter': center_number,
        'search_query': search_query,
    }
    
    return render(request, 'elections/political_entity_agents/list.html', context)


@login_required
def political_entity_agent_add(request):
    """إضافة وكيل كيان سياسي"""
    if request.method == 'POST':
        form = PoliticalEntityAgentForm(request.POST)
        if form.is_valid():
            agent = form.save(commit=False)
            agent.added_by = request.user
            agent.save()
            messages.success(request, f'تم إضافة الوكيل {agent.full_name} بنجاح')
            return redirect('political_entity_agent_detail', pk=agent.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    else:
        # Pre-fill center director if provided
        director_id = request.GET.get('director')
        initial_data = {}
        if director_id:
            director = get_object_or_404(CenterDirector, pk=director_id)
            initial_data = {
                'center_director': director,
                'assigned_center_number': director.assigned_center_number,
                'assigned_center_name': director.assigned_center_name,
                'governorate': director.governorate,
            }
        form = PoliticalEntityAgentForm(initial=initial_data)
    
    context = {
        'form': form,
        'page_title': 'إضافة وكيل كيان سياسي',
    }
    return render(request, 'elections/political_entity_agents/form.html', context)


@login_required
def political_entity_agent_edit(request, pk):
    """تعديل وكيل كيان سياسي"""
    agent = get_object_or_404(PoliticalEntityAgent, pk=pk)
    
    if request.method == 'POST':
        form = PoliticalEntityAgentForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث بيانات {agent.full_name} بنجاح')
            return redirect('political_entity_agent_detail', pk=agent.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    else:
        form = PoliticalEntityAgentForm(instance=agent)
    
    context = {
        'form': form,
        'agent': agent,
        'page_title': f'تعديل الوكيل - {agent.full_name}',
    }
    return render(request, 'elections/political_entity_agents/form.html', context)


@login_required
def political_entity_agent_detail(request, pk):
    """عرض تفاصيل وكيل الكيان السياسي"""
    agent = get_object_or_404(
        PoliticalEntityAgent.objects.select_related('political_entity', 'center_director'),
        pk=pk
    )
    
    context = {
        'agent': agent,
    }
    
    return render(request, 'elections/political_entity_agents/detail.html', context)


@login_required
def political_entity_agent_delete(request, pk):
    """حذف وكيل كيان سياسي"""
    if request.method == 'POST':
        agent = get_object_or_404(PoliticalEntityAgent, pk=pk)
        name = agent.full_name
        agent.delete()
        messages.success(request, f'تم حذف الوكيل {name} بنجاح')
        return redirect('political_entity_agent_list')
    
    return redirect('political_entity_agent_list')


# ==================== AJAX/API Views ====================

@login_required
def get_agents_by_center(request):
    """API للحصول على الوكلاء حسب المركز"""
    center_number = request.GET.get('center_number')
    
    if not center_number:
        return JsonResponse({'agents': []})
    
    agents = PoliticalEntityAgent.objects.filter(
        assigned_center_number=center_number
    ).select_related('political_entity', 'center_director').values(
        'id', 'full_name', 'phone', 'assigned_station_number',
        'political_entity__name', 'status', 'badge_issued'
    )
    
    return JsonResponse({'agents': list(agents)})


@login_required
def get_center_director_by_center(request):
    """API للحصول على مدير المركز حسب رقم المركز"""
    center_number = request.GET.get('center_number')
    
    if not center_number:
        return JsonResponse({'director': None})
    
    try:
        director = CenterDirector.objects.get(assigned_center_number=center_number)
        data = {
            'id': director.id,
            'full_name': director.full_name,
            'phone': director.phone,
            'email': director.email,
            'voting_type': director.get_voting_type_display(),
            'status': director.get_status_display(),
        }
        return JsonResponse({'director': data})
    except CenterDirector.DoesNotExist:
        return JsonResponse({'director': None})

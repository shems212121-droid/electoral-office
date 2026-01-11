"""
User Management Views
إدارة المستخدمين والأدوار
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator

from .models import UserProfile, UserRole, Area, Neighborhood
from .decorators import admin_only


@admin_only
def user_management_list(request):
    """قائمة جميع المستخدمين - Admin فقط"""
    users = User.objects.select_related(
        'profile',
        'profile__linked_candidate',
        'profile__linked_operations_room',
        'profile__assigned_area'
    ).all()
    
    # Filters
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    linked_filter = request.GET.get('linked')  # New filter
    search = request.GET.get('q')
    
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(profile__is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(profile__is_active=False)
    
    # New: Filter by linked entity
    if linked_filter == 'candidate':
        users = users.filter(profile__linked_candidate__isnull=False)
    elif linked_filter == 'room':
        users = users.filter(profile__linked_operations_room__isnull=False)
    elif linked_filter == 'none':
        users = users.filter(
            profile__linked_candidate__isnull=True,
            profile__linked_operations_room__isnull=True
        )
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(profile__employee_id__icontains=search) |
            Q(profile__linked_candidate__full_name__icontains=search) |
            Q(profile__linked_operations_room__name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(users, 30)
    page = request.GET.get('page')
    users_page = paginator.get_page(page)
    
    # Enhanced Statistics
    stats = {
        'total_users': User.objects.count(),
        'active_users': UserProfile.objects.filter(is_active=True).count(),
        'inactive_users': UserProfile.objects.filter(is_active=False).count(),
        'by_role': UserProfile.objects.values('role').annotate(count=Count('id')),
        'linked_to_candidates': UserProfile.objects.filter(linked_candidate__isnull=False).count(),
        'linked_to_rooms': UserProfile.objects.filter(linked_operations_room__isnull=False).count(),
        'no_links': UserProfile.objects.filter(
            linked_candidate__isnull=True,
            linked_operations_room__isnull=True
        ).count(),
    }
    
    context = {
        'users': users_page,
        'stats': stats,
        'roles': UserRole.choices,
        'areas': Area.objects.all(),
        'current_filters': {
            'role': role_filter,
            'status': status_filter,
            'linked': linked_filter,
            'search': search,
        }
    }
    
    return render(request, 'elections/user_management/user_list.html', context)


@admin_only
def user_create(request):
    """إنشاء مستخدم جديد"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Profile fields
        role = request.POST.get('role', UserRole.VIEWER)
        phone = request.POST.get('phone')
        employee_id = request.POST.get('employee_id')
        assigned_area_id = request.POST.get('assigned_area')
        can_export = request.POST.get('can_export') == 'on'
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Update profile
            user.profile.role = role
            user.profile.phone = phone
            user.profile.employee_id = employee_id
            user.profile.can_export_reports = can_export
            
            if assigned_area_id:
                user.profile.assigned_area_id = assigned_area_id
            
            user.profile.save()
            
            messages.success(request, f'تم إنشاء المستخدم {username} بنجاح!')
            return redirect('user_management_list')
            
        except Exception as e:
            messages.error(request, f'خطأ في إنشاء المستخدم: {str(e)}')
    
    context = {
        'roles': UserRole.choices,
        'areas': Area.objects.all(),
    }
    
    return render(request, 'elections/user_management/user_form.html', context)


@admin_only
def user_edit(request, user_id):
    """تعديل مستخدم"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        
        # Update profile
        user.profile.role = request.POST.get('role')
        user.profile.phone = request.POST.get('phone')
        user.profile.employee_id = request.POST.get('employee_id')
        user.profile.can_export_reports = request.POST.get('can_export') == 'on'
        user.profile.can_delete_records = request.POST.get('can_delete') == 'on'
        user.profile.is_active = request.POST.get('is_active') == 'on'
        
        assigned_area_id = request.POST.get('assigned_area')
        if assigned_area_id:
            user.profile.assigned_area_id = assigned_area_id
        else:
            user.profile.assigned_area = None
        
        user.save()
        user.profile.save()
        
        messages.success(request, f'تم تحديث بيانات {user.username} بنجاح!')
        return redirect('user_management_list')
    
    context = {
        'edit_user': user,
        'roles': UserRole.choices,
        'areas': Area.objects.all(),
    }
    
    return render(request, 'elections/user_management/user_form.html', context)


@admin_only
def user_toggle_active(request, user_id):
    """تفعيل/تعطيل مستخدم"""
    from django.utils import timezone
    
    user = get_object_or_404(User, id=user_id)
    user.profile.is_active = not user.profile.is_active
    
    if user.profile.is_active:
        user.profile.activation_date = timezone.now().date()
        user.profile.deactivation_date = None
        messages.success(request, f'تم تفعيل المستخدم {user.username}')
    else:
        user.profile.deactivation_date = timezone.now().date()
        messages.warning(request, f'تم تعطيل المستخدم {user.username}')
    
    user.profile.save()
    
    return redirect('user_management_list')


@admin_only
def user_delete(request, user_id):
    """حذف مستخدم"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'تم حذف المستخدم {username}')
        return redirect('user_management_list')
    
    return render(request, 'elections/user_management/user_confirm_delete.html', {'delete_user': user})


# ==================== Credential Generation ====================

import secrets
import string
from .models import Candidate, SubOperationRoom

def generate_random_password(length=8):
    """Generate a random password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def create_user_with_role(username, password, role, full_name=None, linked_candidate=None, linked_room=None):
    """Helper to create user and profile"""
    try:
        # Create User
        if User.objects.filter(username=username).exists():
            return None, "المستخدم موجود مسبقاً"
            
        user = User.objects.create_user(username=username, password=password)
        if full_name:
            user.first_name = full_name[:30] # Limit length
        user.save()
        
        # Update Profile
        # Profile is created via signal, so we fetch it
        profile = user.profile
        profile.role = role
        if linked_candidate:
            profile.linked_candidate = linked_candidate
        if linked_room:
            profile.linked_operations_room = linked_room
        profile.save()
        
        return user, None
    except Exception as e:
        return None, str(e)

@admin_only
def generate_credentials_view(request):
    """عرض صفحة توليد الحسابات"""
    # Get Candidates who don't have a linked user profile (approximate check)
    # Since it's a ForeignKey, multiple users could link to same candidate, but we assume 1-1 mostly.
    # We display all for now, maybe mark those with existing users.
    candidates = Candidate.objects.all()
    rooms = SubOperationRoom.objects.all()
    
    context = {
        'candidates': candidates,
        'rooms': rooms,
    }
    return render(request, 'elections/user_management/user_generate_credentials.html', context)

@admin_only
def generate_credentials_candidate(request):
    """توليد حساب للمرشح"""
    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')
        generated_list = []
        
        targets = []
        if candidate_id == 'all':
            # Simplified: generate for all candidates who don't have linked profiles
            # For now, just generate for ALL (might be heavy if many) - let's restrict to first 50 or unlinked.
            targets = Candidate.objects.filter(userprofile__isnull=True)[:50]
        else:
            targets = [get_object_or_404(Candidate, id=candidate_id)]
            
        for cand in targets:
            username = f"cand_{cand.candidate_code.replace('-', '')}" if cand.candidate_code else f"cand_{cand.id}"
            password = generate_random_password()
            
            user, error = create_user_with_role(username, password, UserRole.CANDIDATE, 
                                                full_name=cand.full_name, linked_candidate=cand)
            if user:
                generated_list.append({
                    'name': cand.full_name,
                    'username': username,
                    'password': password,
                    'role_display': 'مرشح'
                })
        
        # Render back with results
        context = {
            'candidates': Candidate.objects.all(),
            'rooms': SubOperationRoom.objects.all(),
            'generated_credentials': generated_list
        }
        messages.success(request, f'تم توليد {len(generated_list)} حساب بنجاح')
        return render(request, 'elections/user_management/user_generate_credentials.html', context)
    return redirect('generate_credentials_view')

@admin_only
def generate_credentials_admin(request):
    """توليد حساب إدارة"""
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        
        if not username:
            username = f"admin_{secrets.token_hex(3)}"
            
        password = generate_random_password()
        
        user, error = create_user_with_role(username, password, UserRole.ADMIN, full_name=full_name)
        
        generated_list = []
        if user:
            generated_list.append({
                'name': full_name,
                'username': username,
                'password': password,
                'role_display': 'إدارة (Admin)'
            })
            messages.success(request, 'تم توليد حساب الإدارة بنجاح')
        else:
            messages.error(request, f'خطأ: {error}')
            
        context = {
            'candidates': Candidate.objects.all(),
            'rooms': SubOperationRoom.objects.all(),
            'generated_credentials': generated_list
        }
        return render(request, 'elections/user_management/user_generate_credentials.html', context)
    return redirect('generate_credentials_view')

@admin_only
def generate_credentials_support(request):
    """توليد حساب دعم فني"""
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = f"support_{secrets.token_hex(3)}"
        password = generate_random_password()
        
        user, error = create_user_with_role(username, password, UserRole.TECHNICAL_SUPPORT, full_name=full_name)
        
        generated_list = []
        if user:
            generated_list.append({
                'name': full_name,
                'username': username,
                'password': password,
                'role_display': 'دعم فني'
            })
            messages.success(request, 'تم توليد حساب الدعم الفني بنجاح')
        
        context = {
            'candidates': Candidate.objects.all(),
            'rooms': SubOperationRoom.objects.all(),
            'generated_credentials': generated_list
        }
        return render(request, 'elections/user_management/user_generate_credentials.html', context)
    return redirect('generate_credentials_view')

@admin_only
def generate_credentials_room(request):
    """توليد حساب غرفة عمليات"""
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        generated_list = []
        
        targets = []
        if room_id == 'all':
            targets = SubOperationRoom.objects.filter(userprofile__isnull=True)
        else:
            targets = [get_object_or_404(SubOperationRoom, id=room_id)]
            
        for room in targets:
            username = f"room_{room.room_code.replace('-', '')}" if room.room_code else f"room_{room.id}"
            password = generate_random_password()
            
            user, error = create_user_with_role(username, password, UserRole.OPERATIONS_ROOM, 
                                                full_name=room.name, linked_room=room)
            if user:
                generated_list.append({
                    'name': room.name,
                    'username': username,
                    'password': password,
                    'role_display': 'غرفة عمليات'
                })
        
        context = {
            'candidates': Candidate.objects.all(),
            'rooms': SubOperationRoom.objects.all(),
            'generated_credentials': generated_list
        }
        messages.success(request, f'تم توليد {len(generated_list)} حساب بنجاح')
        return render(request, 'elections/user_management/user_generate_credentials.html', context)
    return redirect('generate_credentials_view')


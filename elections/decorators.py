"""
Decorators للتحقق من الأدوار والصلاحيات
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .models import UserRole


def role_required(allowed_roles):
    """
    Decorator للتحقق من أن المستخدم لديه أحد الأدوار المسموحة
    
    Usage:
        @role_required([UserRole.ADMIN, UserRole.SUPERVISOR])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'لا يوجد ملف تعريف لهذا المستخدم. يرجى التواصل مع المدير.')
                return redirect('dashboard')
            
            # Check if user's role is in allowed roles
            if request.user.profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # User doesn't have permission
            messages.error(request, f'عذراً، لا تملك الصلاحيات الكافية للوصول إلى هذه الصفحة. دورك الحالي: {request.user.profile.get_role_display()}')
            raise PermissionDenied
        
        return wrapper
    return decorator


def permission_required(permission_name):
    """
    Decorator للتحقق من صلاحية محددة
    
    Usage:
        @permission_required('add_voters')
        def add_voter_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'لا يوجد ملف تعريف لهذا المستخدم. يرجى التواصل مع المدير.')
                return redirect('dashboard')
            
            # Check permission
            if request.user.profile.has_permission(permission_name):
                return view_func(request, *args, **kwargs)
            
            # User doesn't have permission
            messages.error(request, f'عذراً، لا تملك الصلاحية المطلوبة: {permission_name}')
            raise PermissionDenied
        
        return wrapper
    return decorator


def admin_only(view_func):
    """
    Decorator للسماح فقط لمدير النظام
    
    Usage:
        @admin_only
        def manage_users_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'لا يوجد ملف تعريف لهذا المستخدم.')
            return redirect('dashboard')
        
        if request.user.profile.role == UserRole.ADMIN:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'هذه الصفحة متاحة فقط لمدير النظام.')
        raise PermissionDenied
    
    return wrapper


def can_export(view_func):
    """
    Decorator للتحقق من صلاحية تصدير التقارير
    
    Usage:
        @can_export
        def export_excel_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'لا يوجد ملف تعريف لهذا المستخدم.')
            return redirect('dashboard')
        
        # Admin and Supervisor can always export
        if request.user.profile.role in [UserRole.ADMIN, UserRole.SUPERVISOR]:
            return view_func(request, *args, **kwargs)
        
        # Others need the specific permission
        if request.user.profile.can_export_reports:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'ليس لديك صلاحية تصدير التقارير.')
        raise PermissionDenied
    
    return wrapper


def can_delete(view_func):
    """
    Decorator للتحقق من صلاحية الحذف
    
    Usage:
        @can_delete
        def delete_voter_view(request, pk):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'لا يوجد ملف تعريف لهذا المستخدم.')
            return redirect('dashboard')
        
        # Only admin can delete
        if request.user.profile.role == UserRole.ADMIN or request.user.profile.can_delete_records:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'ليس لديك صلاحية حذف السجلات. فقط مدير النظام يمكنه ذلك.')
        raise PermissionDenied
    
    return wrapper


# Context processor to make user profile available in all templates
def user_profile_context(request):
    """
    Context processor لإضافة معلومات المستخدم والصلاحيات لجميع القوالب
    
    Add to settings.py TEMPLATES OPTIONS context_processors:
        'elections.decorators.user_profile_context',
    """
    try:
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            return {
                'user_profile': request.user.profile,
                'user_role': request.user.profile.role,
                'user_role_display': request.user.profile.get_role_display(),
                'is_admin': request.user.profile.role == UserRole.ADMIN,
                'is_supervisor': request.user.profile.role == UserRole.SUPERVISOR,
                'can_export': request.user.profile.has_permission('export_reports'),
            }
    except Exception:
        pass
        
    return {
        'user_profile': None,
        'user_role': None,
        'user_role_display': 'غير محدد',
        'is_admin': False,
        'is_supervisor': False,
        'can_export': False,
    }

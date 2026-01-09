"""
Role-Based Dashboard Views
لوحات التحكم المخصصة حسب الأدوار
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    UserRole, Voter, Candidate, Anchor, Introducer, 
    CampaignTask, CommunicationLog, PartyCandidate, VoteCount
)
from .decorators import role_required


@role_required([UserRole.ADMIN])
def admin_dashboard(request):
    """لوحة تحكم مدير النظام"""
    context = {
        'total_users': User.objects.count(),
        'active_users': UserProfile.objects.filter(is_active=True).count(),
        'total_voters': Voter.objects.count(),
        'total_candidates': Candidate.objects.count(),
        'total_tasks': CampaignTask.objects.count(),
        'pending_tasks': CampaignTask.objects.filter(status='pending').count(),
        
        # Recent activities
        'recent_users': User.objects.select_related('profile').order_by('-date_joined')[:10],
        'recent_tasks': CampaignTask.objects.order_by('-created_at')[:10],
    }
    
    return render(request, 'elections/dashboards/admin_dashboard.html', context)


@role_required([UserRole.SUPERVISOR])
def supervisor_dashboard(request):
    """لوحة تحكم المشرف"""
    context = {
        'total_voters': Voter.objects.count(),
        'assigned_voters': Voter.objects.filter(introducer__isnull=False).count(),
        'total_candidates': Candidate.objects.count(),
        'total_anchors': Anchor.objects.count(),
        'total_introducers': Introducer.objects.count(),
        
        # Statistics
        'supporters': Voter.objects.filter(classification='supporter').count(),
        'neutrals': Voter.objects.filter(classification='neutral').count(),
        'opponents': Voter.objects.filter(classification='opponent').count(),
        
        # Recent
        'recent_communications': CommunicationLog.objects.select_related('voter', 'user').order_by('-created_at')[:15],
        'recent_tasks': CampaignTask.objects.filter(
            Q(assigned_to=request.user) | Q(created_by=request.user)
        ).order_by('-created_at')[:10],
    }
    
    return render(request, 'elections/dashboards/supervisor_dashboard.html', context)


@role_required([
    UserRole.DATA_ENTRY_VOTERS,
    UserRole.DATA_ENTRY_CANDIDATES,
    UserRole.DATA_ENTRY_MONITORS,
    UserRole.DATA_ENTRY_ANCHORS,
    UserRole.DATA_ENTRY_INTRODUCERS
])
def data_entry_dashboard(request):
    """لوحة تحكم مدخلي البيانات"""
    user_role = request.user.profile.role
    
    context = {
        'user_role': user_role,
        'user_role_display': request.user.profile.get_role_display(),
    }
    
    # Statistics based on role
    if user_role == UserRole.DATA_ENTRY_VOTERS:
        context['total_count'] = Voter.objects.count()
        context['my_entries'] = Voter.objects.filter(created_at__date__gte=timezone.now().date()).count()
        context['recent_items'] = Voter.objects.order_by('-created_at')[:20]
        context['entry_type'] = 'voters'
        
    elif user_role == UserRole.DATA_ENTRY_CANDIDATES:
        context['total_count'] = PartyCandidate.objects.count()
        context['my_entries'] = PartyCandidate.objects.filter(created_at__date__gte=timezone.now().date()).count()
        context['recent_items'] = PartyCandidate.objects.select_related('party').order_by('-created_at')[:20]
        context['entry_type'] = 'candidates'
        
    elif user_role == UserRole.DATA_ENTRY_ANCHORS:
        context['total_count'] = Anchor.objects.count()
        context['my_entries'] = Anchor.objects.filter(created_at__date__gte=timezone.now().date()).count()
        context['recent_items'] = Anchor.objects.select_related('candidate').order_by('-created_at')[:20]
        context['entry_type'] = 'anchors'
        
    elif user_role == UserRole.DATA_ENTRY_INTRODUCERS:
        context['total_count'] = Introducer.objects.count()
        context['my_entries'] = Introducer.objects.filter(created_at__date__gte=timezone.now().date()).count()
        context['recent_items'] = Introducer.objects.select_related('anchor').order_by('-created_at')[:20]
        context['entry_type'] = 'introducers'
    
    # Tasks assigned to this user
    context['my_tasks'] = CampaignTask.objects.filter(assigned_to=request.user).order_by('-created_at')[:5]
    
    return render(request, 'elections/dashboards/data_entry_dashboard.html', context)


@role_required([UserRole.VIEWER])
def viewer_dashboard(request):
    """لوحة تحكم المستعرض (قراءة فقط)"""
    context = {
        'total_voters': Voter.objects.count(),
        'total_candidates': Candidate.objects.count(),
        'total_anchors': Anchor.objects.count(),
        'total_introducers': Introducer.objects.count(),
        
        # Statistics
        'supporters': Voter.objects.filter(classification='supporter').count(),
        'neutrals': Voter.objects.filter(classification='neutral').count(),
        'opponents': Voter.objects.filter(classification='opponent').count(),
        
        # Vote counts
        'total_votes': VoteCount.objects.count(),
        'top_candidates': PartyCandidate.objects.annotate(
            total_votes=Count('vote_counts')
        ).order_by('-total_votes')[:10],
    }
    
    return render(request, 'elections/dashboards/viewer_dashboard.html', context)


from django.contrib.auth.models import User
from .models import (
    UserProfile, SubOperationRoom, CandidateMonitor, CenterDirector, PoliticalEntityAgent
)


@role_required([UserRole.CANDIDATE])
def candidate_dashboard(request):
    """لوحة تحكم المرشح"""
    try:
        profile = request.user.profile
        candidate = profile.linked_candidate
        
        if not candidate:
            return render(request, 'elections/dashboards/error.html', {'message': 'لم يتم ربط حسابك بملف مرشح'})
            
        context = {
            'candidate': candidate,
            'anchors_count': candidate.anchors.count(),
            'introducers_count': Introducer.objects.filter(anchor__candidate=candidate).count(),
            'voters_count': Voter.objects.filter(introducer__anchor__candidate=candidate).count(),
            'monitors_count': candidate.monitors.count(),
            
            # Lists
            'anchors': candidate.anchors.all(),
            'monitors': candidate.monitors.all(),
            # For introducers and voters, we might need separate pages if too many, but here is a simple list or summary
            'introducers': Introducer.objects.filter(anchor__candidate=candidate)[:20],
        }
        return render(request, 'elections/dashboards/candidate_dashboard.html', context)
    except Exception as e:
         return render(request, 'elections/dashboards/error.html', {'message': f'حدث خطأ: {str(e)}'})

@role_required([UserRole.TECHNICAL_SUPPORT])
def tech_support_dashboard(request):
    """لوحة تحكم الدعم الفني"""
    context = {
        'candidates': Candidate.objects.all(),
        'operations_rooms': SubOperationRoom.objects.all(),
        'total_candidates': Candidate.objects.count(),
        'total_rooms': SubOperationRoom.objects.count(),
    }
    return render(request, 'elections/dashboards/tech_support_dashboard.html', context)

@role_required([UserRole.OPERATIONS_ROOM])
def operations_room_dashboard(request):
    """لوحة تحكم غرفة العمليات"""
    try:
        profile = request.user.profile
        room = profile.linked_operations_room
        
        if not room:
            return render(request, 'elections/dashboards/error.html', {'message': 'لم يتم ربط حسابك بغرفة عمليات'})
            
        context = {
            'room': room,
            'voters_count': room.get_voters_count(),
            'agents_count': room.get_agents_count(),
            'directors_count': room.get_directors_count(),
            
            # Lists
            'directors': room.directors.all(),
            'agents': room.agents.all(),
            'recent_voters': Voter.objects.filter(introducer__sub_room=room).order_by('-updated_at')[:20],
        }
        return render(request, 'elections/dashboards/operations_room_dashboard.html', context)
    except Exception as e:
        return render(request, 'elections/dashboards/error.html', {'message': f'حدث خطأ: {str(e)}'})

@role_required([UserRole.TECHNICAL_SUPPORT])
def tech_support_dashboard(request):
    """لوحة تحكم الدعم الفني"""
    context = {
        'total_users': User.objects.count(),
        'total_voters': Voter.objects.count(),
        'total_candidates': Candidate.objects.count(),
        'communications_count': CommunicationLog.objects.count(),
        'tasks_count': CampaignTask.objects.count(),
        
        # Recent logs for debugging
        'recent_logs': CommunicationLog.objects.order_by('-created_at')[:20],
    }
    return render(request, 'elections/dashboards/tech_support_dashboard.html', context)


@role_required([UserRole.OPERATIONS_ROOM])
def operations_room_dashboard(request):
    """لوحة تحكم غرفة العمليات"""
    # Should show data related to their assigned area or room
    # For now, generalized view
    context = {
        'total_voters': Voter.objects.count(),
        'total_anchors': Anchor.objects.count(),
        'total_introducers': Introducer.objects.count(),
        
        'pending_tasks': CampaignTask.objects.filter(status='pending').count(),
        'in_progress_tasks': CampaignTask.objects.filter(status='in_progress').count(),
        
        'recent_tasks': CampaignTask.objects.filter(
            Q(assigned_to=request.user) | Q(created_by=request.user)
        ).order_by('-created_at')[:10],
    }
    return render(request, 'elections/dashboards/operations_room_dashboard.html', context)

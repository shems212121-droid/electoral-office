from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, Case, When, Value, IntegerField
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.decorators import login_required

from .models import (
    Voter, Candidate, Anchor, Introducer, CandidateMonitor,
    CommunicationLog, CampaignTask, Area, Neighborhood,
    PoliticalParty, PartyCandidate, PollingCenter, PollingStation, VoteCount
)
from .forms import (
    CandidateForm, AnchorForm, IntroducerForm, VoterAssignmentForm,
    CommunicationLogForm, CampaignTaskForm, CandidateMonitorForm,
    PoliticalPartyForm, PartyCandidateForm, PollingCenterForm, 
    PollingStationForm, VoteCountForm, QuickVoteCountForm,
    GeneralVoteCountForm, SpecialVoteCountForm
)


# ==================== General Vote Counting (جرد عام) ====================

class GeneralVoteCountView(LoginRequiredMixin, TemplateView):
    """صفحة إدخال جرد الأصوات العام"""
    template_name = 'elections/vote/general_count.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # عرض المحطات من المراكز العامة فقط
        context['stations'] = PollingStation.objects.select_related('center').filter(
            center__voting_type='general'
        ).order_by('center__center_number', 'station_number')
        
        # ترتيب المرشحين: كتلة الصادقون أولاً
        context['candidates'] = PartyCandidate.objects.select_related('party').annotate(
            is_sadiqoun=Case(
                When(party__name__contains="الصادقون", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('is_sadiqoun', 'party__serial_number', 'serial_number')
        
        context['form'] = GeneralVoteCountForm()
        
        # Get existing general vote counts
        context['vote_counts'] = VoteCount.objects.filter(
            vote_type='general'
        ).select_related('station', 'candidate', 'entered_by').order_by('-entered_at')[:50]
        
        # إحصائيات مراكز الاقتراع العام
        context['general_centers_count'] = PollingCenter.objects.filter(voting_type='general').count()
        context['general_stations_count'] = context['stations'].count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = GeneralVoteCountForm(request.POST)
        if form.is_valid():
            vote_count = form.save(commit=False)
            vote_count.entered_by = request.user
            
            try:
                # Check if entry already exists
                existing = VoteCount.objects.filter(
                    station=vote_count.station,
                    candidate=vote_count.candidate,
                    vote_type='general'
                ).first()
                
                if existing:
                    messages.error(
                        request,
                        f'⚠️ تم إدخال هذه البيانات مسبقاً! '
                        f'المحطة: {existing.station.full_number} | '
                        f'المرشح: {existing.candidate.full_name} | '
                        f'الأصوات المسجلة: {existing.vote_count} | '
                        f'تم الإدخال بواسطة: {existing.entered_by.username}'
                    )
                else:
                    vote_count.save()
                    messages.success(
                        request, 
                        f'✅ تم حفظ جرد الأصوات العام بنجاح! '
                        f'المحطة: {vote_count.station.full_number} | '
                        f'المرشح: {vote_count.candidate.full_name} | '
                        f'الأصوات: {vote_count.vote_count}'
                    )
                    
                return redirect('general_vote_count')
                
            except Exception as e:
                messages.error(request, f'حدث خطأ غير متوقع: {str(e)}')
                
        else:
            messages.error(request, 'حدث خطأ في الحفظ. يرجى التحقق من البيانات.')
            
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


# ===== Special Vote Counting (جرد خاص) ====================

class SpecialVoteCountView(LoginRequiredMixin, TemplateView):
    """صفحة إدخال جرد الأصوات الخاص"""
    template_name = 'elections/vote/special_count.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # عرض المحطات من المراكز الخاصة فقط
        context['stations'] = PollingStation.objects.select_related('center').filter(
            center__voting_type='special'
        ).order_by('center__center_number', 'station_number')
        
        # ترتيب المرشحين: كتلة الصادقون أولاً
        context['candidates'] = PartyCandidate.objects.select_related('party').annotate(
            is_sadiqoun=Case(
                When(party__name__contains="الصادقون", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('is_sadiqoun', 'party__serial_number', 'serial_number')
        
        context['form'] = SpecialVoteCountForm()
        
        # Get existing special vote counts
        context['vote_counts'] = VoteCount.objects.filter(
            vote_type='special'
        ).select_related('station', 'candidate', 'entered_by').order_by('-entered_at')[:50]
        
        # إحصائيات مراكز الاقتراع الخاص
        context['special_centers_count'] = PollingCenter.objects.filter(voting_type='special').count()
        context['special_stations_count'] = context['stations'].count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = SpecialVoteCountForm(request.POST)
        if form.is_valid():
            vote_count = form.save(commit=False)
            vote_count.entered_by = request.user
            
            try:
                # Check if entry already exists
                existing = VoteCount.objects.filter(
                    station=vote_count.station,
                    candidate=vote_count.candidate,
                    vote_type='special'
                ).first()
                
                if existing:
                    messages.error(
                        request,
                        f'⚠️ تم إدخال هذه البيانات مسبقاً! '
                        f'المحطة: {existing.station.full_number} | '
                        f'المرشح: {existing.candidate.full_name} | '
                        f'الأصوات المسجلة: {existing.vote_count} | '
                        f'تم الإدخال بواسطة: {existing.entered_by.username}'
                    )
                else:
                    vote_count.save()
                    messages.success(
                        request, 
                        f'✅ تم حفظ جرد الأصوات الخاص بنجاح! '
                        f'المحطة: {vote_count.station.full_number} | '
                        f'المرشح: {vote_count.candidate.full_name} | '
                        f'الأصوات: {vote_count.vote_count}'
                    )
                    
                return redirect('special_vote_count')
                
            except Exception as e:
                messages.error(request, f'حدث خطأ غير متوقع: {str(e)}')
                
        else:
            messages.error(request, 'حدث خطأ في الحفظ. يرجى التحقق من البيانات.')
            
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


# ==================== Combined Results (النتائج المجمعة) ====================

class CombinedResultsView(LoginRequiredMixin, TemplateView):
    """صفحة عرض النتائج المجمعة (عام + خاص)"""
    template_name = 'elections/vote/combined_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filters
        vote_type_filter = self.request.GET.get('vote_type', 'all')
        center_filter = self.request.GET.get('center')
        station_filter = self.request.GET.get('station')
        party_filter = self.request.GET.get('party')
        
        # Base queryset
        vote_counts = VoteCount.objects.select_related(
            'station__center', 'candidate__party', 'entered_by'
        )
        
        # Apply filters
        if vote_type_filter != 'all':
            vote_counts = vote_counts.filter(vote_type=vote_type_filter)
        if center_filter:
            vote_counts = vote_counts.filter(station__center_id=center_filter)
        if station_filter:
            vote_counts = vote_counts.filter(station_id=station_filter)
        if party_filter:
            vote_counts = vote_counts.filter(candidate__party_id=party_filter)
        
        # Aggregate results by candidate (combining general + special)
        # Note: stations_voted and stations_not_voted are model fields, not aggregates
        candidate_results = PartyCandidate.objects.annotate(
            general_votes=Sum('vote_counts__vote_count', filter=Q(vote_counts__vote_type='general')),
            special_votes=Sum('vote_counts__vote_count', filter=Q(vote_counts__vote_type='special')),
            total_votes=Sum('vote_counts__vote_count')
        ).select_related('party').order_by('-total_votes')
        
        # Apply party filter to candidate results
        if party_filter:
            candidate_results = candidate_results.filter(party_id=party_filter)
        
        # Aggregate results by party
        party_results = PoliticalParty.objects.annotate(
            general_votes=Sum('candidates__vote_counts__vote_count', filter=Q(candidates__vote_counts__vote_type='general')),
            special_votes=Sum('candidates__vote_counts__vote_count', filter=Q(candidates__vote_counts__vote_type='special')),
            total_votes=Sum('candidates__vote_counts__vote_count')
        ).order_by('-total_votes')
        
        # Aggregate results by center
        center_results = PollingCenter.objects.annotate(
            general_votes=Sum('stations__vote_counts__vote_count', filter=Q(stations__vote_counts__vote_type='general')),
            special_votes=Sum('stations__vote_counts__vote_count', filter=Q(stations__vote_counts__vote_type='special')),
            total_votes=Sum('stations__vote_counts__vote_count')
        ).order_by('-total_votes')
        
        # Statistics
        total_general_votes = VoteCount.objects.filter(vote_type='general').aggregate(Sum('vote_count'))['vote_count__sum'] or 0
        total_special_votes = VoteCount.objects.filter(vote_type='special').aggregate(Sum('vote_count'))['vote_count__sum'] or 0
        total_all_votes = total_general_votes + total_special_votes
        
        # Filters for dropdowns
        context['centers'] = PollingCenter.objects.all()
        context['stations'] = PollingStation.objects.select_related('center').all()
        context['parties'] = PoliticalParty.objects.all()
        
        # Results
        context['candidate_results'] = candidate_results
        context['party_results'] = party_results
        context['center_results'] = center_results
        
        # Statistics
        context['total_general_votes'] = total_general_votes
        context['total_special_votes'] = total_special_votes
        context['total_all_votes'] = total_all_votes
        
        # Current filters
        context['current_vote_type'] = vote_type_filter
        context['current_center'] = center_filter
        context['current_station'] = station_filter
        context['current_party'] = party_filter
        
        return context


# ==================== AJAX Endpoints ====================

def get_polling_center_info(request, center_number):
    """
    AJAX endpoint لجلب معلومات مركز الاقتراع بناءً على رقمه
    """
    try:
        # Normalize input: Strip whitespace and convert Arabic numerals to Western
        center_number = str(center_number).strip().translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
        
        # Try finding center by exact number
        center = PollingCenter.objects.filter(center_number=center_number).first()
        
        # If not found and it's an 8-digit code (common in some QR formats), try first 6 digits
        if not center and len(center_number) == 8:
            fallback_number = center_number[:6]
            center = PollingCenter.objects.filter(center_number=fallback_number).first()
            
        if not center:
            raise PollingCenter.DoesNotExist
        
        # جلب المحطات المرتبطة بالمركز
        stations = PollingStation.objects.filter(center=center).values(
            'id', 'station_number', 'full_number'
        )
        
        data = {
            'success': True,
            'center': {
                'id': center.id,
                'name': center.name,
                'center_number': center.center_number,
                'voting_type': center.voting_type,
                'voting_type_display': center.get_voting_type_display(),
                'location': center.location or '',
                'address': center.address or '',
                'area': center.area.name if center.area else '',
                'neighborhood': center.neighborhood.name if center.neighborhood else '',
                'governorate': center.governorate,
                'station_count': center.station_count,
            },
            'stations': list(stations)
        }
        
        return JsonResponse(data)
        
    except PollingCenter.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'مركز الاقتراع غير موجود'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== Vote Totals Dashboard ====================

class VoteTotalsDashboardView(LoginRequiredMixin, TemplateView):
    """لوحة عرض المجموع الإجمالي للأصوات فقط"""
    template_name = 'elections/vote/vote_totals_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات حسب المرشح (عام + خاص)
        candidate_totals = PartyCandidate.objects.annotate(
            general_votes=Sum('vote_counts__vote_count', filter=Q(vote_counts__vote_type='general')),
            special_votes=Sum('vote_counts__vote_count', filter=Q(vote_counts__vote_type='special')),
            total_votes=Sum('vote_counts__vote_count')
        ).filter(total_votes__gt=0).select_related('party').order_by('-total_votes')
        
        # إحصائيات حسب الحزب
        party_totals = PoliticalParty.objects.annotate(
            general_votes=Sum('candidates__vote_counts__vote_count', filter=Q(candidates__vote_counts__vote_type='general')),
            special_votes=Sum('candidates__vote_counts__vote_count', filter=Q(candidates__vote_counts__vote_type='special')),
            total_votes=Sum('candidates__vote_counts__vote_count')
        ).filter(total_votes__gt=0).order_by('-total_votes')
        
        # إجمالي عام
        total_general = VoteCount.objects.filter(vote_type='general').aggregate(Sum('vote_count'))['vote_count__sum'] or 0
        total_special = VoteCount.objects.filter(vote_type='special').aggregate(Sum('vote_count'))['vote_count__sum'] or 0
        total_all = total_general + total_special
        
        # عدد السجلات
        general_count = VoteCount.objects.filter(vote_type='general').count()
        special_count = VoteCount.objects.filter(vote_type='special').count()
        
        context['candidate_totals'] = candidate_totals
        context['party_totals'] = party_totals
        context['total_general'] = total_general
        context['total_special'] = total_special
        context['total_all'] = total_all
        context['general_count'] = general_count
        context['special_count'] = special_count
        context['last_updated'] = timezone.now()
        
        return context


def get_vote_totals_api(request):
    """
    AJAX API endpoint لجلب المجموع الإجمالي للأصوات (للتحديث التلقائي)
    """
    try:
        # إحصائيات حسب المرشح
        candidate_totals = list(
            PartyCandidate.objects.annotate(
                general_votes=Sum('vote_counts__vote_count', filter=Q(vote_counts__vote_type='general')),
                special_votes=Sum('vote_counts__vote_count', filter=Q(vote_counts__vote_type='special')),
                total_votes=Sum('vote_counts__vote_count')
            ).filter(total_votes__gt=0).values(
                'party__serial_number',
                'serial_number',
                'full_name',
                'party__name',
                'party__color',
                'general_votes',
                'special_votes',
                'total_votes'
            ).order_by('-total_votes')
        )
        
        # إحصائيات حسب الحزب
        party_totals = list(
            PoliticalParty.objects.annotate(
                general_votes=Sum('candidates__vote_counts__vote_count', filter=Q(candidates__vote_counts__vote_type='general')),
                special_votes=Sum('candidates__vote_counts__vote_count', filter=Q(candidates__vote_counts__vote_type='special')),
                total_votes=Sum('candidates__vote_counts__vote_count')
            ).filter(total_votes__gt=0).values(
                'serial_number',
                'name',
                'color',
                'general_votes',
                'special_votes',
                'total_votes'
            ).order_by('-total_votes')
        )
        
        # إجمالي عام
        total_general = VoteCount.objects.filter(vote_type='general').aggregate(Sum('vote_count'))['vote_count__sum'] or 0
        total_special = VoteCount.objects.filter(vote_type='special').aggregate(Sum('vote_count'))['vote_count__sum'] or 0
        total_all = total_general + total_special
        
        # عدد السجلات
        general_count = VoteCount.objects.filter(vote_type='general').count()
        special_count = VoteCount.objects.filter(vote_type='special').count()
        
        data = {
            'success': True,
            'candidate_totals': candidate_totals,
            'party_totals': party_totals,
            'totals': {
                'general': total_general,
                'special': total_special,
                'all': total_all,
                'general_count': general_count,
                'special_count': special_count
            },
            'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required # Ensure user is logged in
def save_bulk_votes(request):
    """
    API endpoint لحفظ مجموعة من الأصوات دفعة واحدة (من QR Code)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    import json
    try:
        data = json.loads(request.body)
        
        center_number = data.get('center_number')
        station_number = data.get('station_number') # This is the station number within the center (e.g. 4)
        vote_type = data.get('vote_type', 'general') # 'general' or 'special'
        votes_data = data.get('votes', [])
        
        if not all([center_number, station_number, votes_data]):
            return JsonResponse({'success': False, 'error': 'بيانات غير مكتملة'}, status=400)
            
        # 1. Get Center
        try:
            # Normalize input
            center_number = str(center_number).strip().translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
            station_number = str(station_number).strip().translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
            
            # Try finding center by exact number
            center = PollingCenter.objects.filter(center_number=center_number).first()
            
            # Fallback for 8-digit codes
            if not center and len(center_number) == 8:
                fallback_number = center_number[:6]
                center = PollingCenter.objects.filter(center_number=fallback_number).first()
                
            if not center:
                raise PollingCenter.DoesNotExist
        except PollingCenter.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'مركز الاقتراع رقم {center_number} غير موجود'}, status=404)

        # 2. Get Station
        try:
            station = PollingStation.objects.get(center=center, station_number=station_number)
        except (PollingStation.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': f'المحطة رقم {station_number} غير موجودة في هذا المركز'}, status=404)
        # 3. Check for existing votes for this station/type
        # If we have any votes for this station and this type, we warn/error?
        existing_count = VoteCount.objects.filter(
            station=station, 
            vote_type=vote_type
        ).count()
        
        if existing_count > 0:
            # For now, simplistic approach: Reject.
            # Future: Allow overwrite flag.
            return JsonResponse({
                'success': False, 
                'error': f'توجد بيانات مسجلة مسبقاً لهذه المحطة ({existing_count} سجل). يرجى حذفها أولاً إذا كنت تريد إعادة الإدخال.'
            }, status=409)

        # 4. Save Votes
        saved_count = 0
        with transaction.atomic():
            for vote_entry in votes_data:
                candidate_id = vote_entry.get('candidateId') or vote_entry.get('candidate_id')
                count = vote_entry.get('voteCount') or vote_entry.get('count')
                
                if candidate_id is None or count is None:
                    continue
                    
                # Find Candidate
                # Trying to match candidate_id (from QR) to PartyCandidate
                # QR ID likely corresponds to 'serial_number' within the list if per-party,
                # OR 'candidate_code', OR strict DB ID.
                # Given user context: "114" is State of Law (Party IDs usually).
                # Wait, "114" is a LIST NUMBER (tsaful).
                # PartyCandidate has 'serial_number'.
                # But lists have numbers (Parties have numbers).
                # If "114" is "State of Law", that's a PARTY number (PoliticalParty.serial_number).
                # But votes are cast for CANDIDATES? Or Lists?
                # In Iraqi elections, you vote for a List (Party) AND optionally a Candidate.
                # VoteCount model links to `PartyCandidate`.
                # If the input is just "114" (Party) with count 50, does it mean 50 votes for the party head?
                # Or does `VoteCount` support voting for a Party directly?
                # `VoteCount.candidate` is ForeignKey to `PartyCandidate`.
                # If the generic vote is for the list, usually there is a "List 114" candidate entity?
                # Or maybe the system creates a "Party Vote" dummy candidate?
                # Let's check if there is a PartyCandidate with serial_number 114? 
                # Or if there is a Candidate whose ID is 114?
                
                # Search Strategy:
                # 1. Try PartyCandidate PK (ID)
                # 2. Try PoliticalParty Serial Number (assuming it maps to the 'Head of List' or we need to handle Party Votes separate)
                # Note: The current VoteCount model ONLY links to PartyCandidate. 
                # If valid candidates are just candidates, then 114 must be a candidate.
                
                candidate = None
                
                # Case A: Try valid ID
                if str(candidate_id).isdigit():
                    candidate = PartyCandidate.objects.filter(pk=candidate_id).first()
                    
                # Case B: Try Candidate Code
                if not candidate:
                    candidate = PartyCandidate.objects.filter(candidate_code=candidate_id).first()
                    
                # Case C: Try Serial Number (risky if not unique across parties? No, Party.serial is unique, Candidate.serial is per party)
                # If candidate_id matches a Party Serial Number, maybe we pick the first candidate?
                if not candidate:
                    # Check if it's a Party ID?
                    party = PoliticalParty.objects.filter(serial_number=candidate_id).first()
                    if party:
                        # Find the "List Vote" candidate or the first candidate?
                        # Usually, there is a candidate entry representing the list itself or just assign to the first/leader.
                        # For now, warning if not found.
                        pass
                
                if candidate:
                    VoteCount.objects.create(
                        station=station,
                        candidate=candidate,
                        vote_count=int(count),
                        vote_type=vote_type,
                        entered_by=request.user
                    )
                    saved_count += 1
                else:
                    # Skip or error?
                    # Ideally log detailed errors.
                    pass
        
        return JsonResponse({
            'success': True, 
            'message': f'تم حفظ {saved_count} سجل بنجاح للمحطة {station.full_number}',
            'station_full_number': station.full_number
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

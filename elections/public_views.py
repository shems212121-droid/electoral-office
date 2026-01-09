"""
Public Views for Electoral Office Application
Based on video demonstrations:
- Video 1 (16-52-51.mp4): Electoral Public Registration
- Video 2 (17-02-52.mp4): Personal Voter Record
- Video 3 (17-05-27.mp4): Observer Registration
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
import json
import sqlite3
import os

from .models import (
    ElectoralPublic, PersonalVoterRecord, IntroducerVoter, ObserverRegistration,
    Candidate, Anchor, Introducer, Voter
)
from .forms import (
    ElectoralPublicForm, PersonalVoterRecordForm, IntroducerVoterForm, QuickAddVoterForm, ObserverRegistrationForm
)


# ==================== Electoral Public Views (المرتكزات) ====================
# Based on Video 1: 16-52-51.mp4

class ElectoralPublicListView(LoginRequiredMixin, ListView):
    """عرض قائمة المرتكزات"""
    model = ElectoralPublic
    template_name = 'elections/electoral_public_list.html'
    context_object_name = 'registrations'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = ElectoralPublic.objects.all()
        
        # Search filter
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(voter_number__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(reference_code__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-registered_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['total_count'] = ElectoralPublic.objects.count()
        context['pending_count'] = ElectoralPublic.objects.filter(status='pending').count()
        context['approved_count'] = ElectoralPublic.objects.filter(status='approved').count()
        return context


class ElectoralPublicCreateView(LoginRequiredMixin, CreateView):
    """تسجيل جمهور انتخابي جديد"""
    model = ElectoralPublic
    form_class = ElectoralPublicForm
    template_name = 'elections/electoral_public_form.html'
    success_url = reverse_lazy('electoral_public_list')
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        
        # Link to anchor/candidate based on reference_code
        if instance.reference_code:
            # Try to find anchor
            anchor = Anchor.objects.filter(anchor_code=instance.reference_code).first()
            if anchor:
                instance.linked_anchor = anchor
                instance.linked_candidate = anchor.candidate
            else:
                # Try to find candidate
                candidate = Candidate.objects.filter(candidate_code=instance.reference_code).first()
                if candidate:
                    instance.linked_candidate = candidate
        
        instance.save()
        messages.success(self.request, 'تم تسجيل المرتكز بنجاح!')
        return redirect(self.success_url)


class ElectoralPublicDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل تسجيل المرتكز"""
    model = ElectoralPublic
    template_name = 'elections/electoral_public_detail.html'
    context_object_name = 'registration'


from django.views.generic import UpdateView


class ElectoralPublicUpdateView(LoginRequiredMixin, UpdateView):
    """تعديل بيانات المرتكز"""
    model = ElectoralPublic
    form_class = ElectoralPublicForm
    template_name = 'elections/electoral_public_form.html'
    success_url = reverse_lazy('electoral_public_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث بيانات المرتكز بنجاح!')
        return super().form_valid(form)
 


class ElectoralPublicDeleteView(LoginRequiredMixin, DeleteView):
    """حذف مرتكز"""
    model = ElectoralPublic
    success_url = reverse_lazy('electoral_public_list')
    
    def post(self, request, *args, **kwargs):
        anchor = self.get_object()
        voter_number = anchor.voter_number
        anchor.delete()
        messages.success(request, f'تم حذف المرتكز برقم ناخب: {voter_number}')
        return redirect(self.success_url)


@login_required
def approve_electoral_public(request, pk):
    """الموافقة على تسجيل المرتكز"""
    registration = get_object_or_404(ElectoralPublic, pk=pk)
    registration.status = 'active'
    registration.save()
    messages.success(request, f'تم تفعيل المرتكز: {registration.voter_number}')
    return redirect('electoral_public_list')


@login_required
def reject_electoral_public(request, pk):
    """رفض تسجيل المرتكز"""
    registration = get_object_or_404(ElectoralPublic, pk=pk)
    registration.status = 'inactive'
    registration.save()
    messages.warning(request, f'تم تعطيل المرتكز: {registration.voter_number}')
    return redirect('electoral_public_list')


# ==================== Introducer Views (المعرفين) ====================

class PersonalVoterRecordView(LoginRequiredMixin, ListView):
    """عرض قائمة المعرفين"""
    model = PersonalVoterRecord
    template_name = 'elections/introducer_list.html'
    context_object_name = 'introducers'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = PersonalVoterRecord.objects.all()
        
        # Search filter
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(voter_number__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(anchor_code__icontains=search)
            )
        
        # Classification filter
        classification = self.request.GET.get('classification', '')
        if classification:
            queryset = queryset.filter(classification=classification)
        
        return queryset.select_related('anchor', 'anchor__candidate').order_by('-added_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['classification_filter'] = self.request.GET.get('classification', '')
        context['total_count'] = PersonalVoterRecord.objects.count()
        context['supporter_count'] = PersonalVoterRecord.objects.filter(classification='supporter').count()
        return context


class IntroducerCreateView(LoginRequiredMixin, CreateView):
    """إضافة معرف جديد"""
    model = PersonalVoterRecord
    form_class = PersonalVoterRecordForm
    template_name = 'elections/introducer_form.html'
    success_url = reverse_lazy('personal_voter_record')
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        
        # ربط بالمرتكز عبر كود المرتكز
        if instance.anchor_code:
            # البحث عن المرتكز برقم الناخب
            anchor = ElectoralPublic.objects.filter(voter_number=instance.anchor_code).first()
            if anchor:
                instance.anchor = anchor
            else:
                messages.warning(self.request, 'لم يتم العثور على مرتكز بهذا الكود')
        
        instance.save()
        messages.success(self.request, f'تم إضافة المعرف: {instance.full_name}')
        return redirect(self.success_url)


class IntroducerUpdateView(LoginRequiredMixin, UpdateView):
    """تعديل معرف"""
    model = PersonalVoterRecord
    form_class = PersonalVoterRecordForm
    template_name = 'elections/introducer_form.html'
    success_url = reverse_lazy('personal_voter_record')
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        
        # تحديث ربط المرتكز
        if instance.anchor_code:
            anchor = ElectoralPublic.objects.filter(voter_number=instance.anchor_code).first()
            if anchor:
                instance.anchor = anchor
        
        instance.save()
        messages.success(self.request, 'تم تحديث بيانات المعرف بنجاح!')
        return redirect(self.success_url)


class IntroducerDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل المعرف وناخبيه"""
    model = PersonalVoterRecord
    template_name = 'elections/introducer_detail.html'
    context_object_name = 'introducer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        introducer = self.get_object()
        context['voters'] = introducer.voters.all().order_by('-added_at')
        context['voters_count'] = introducer.voters.count()
        context['supporter_count'] = introducer.voters.filter(classification='supporter').count()
        return context


@login_required
def delete_introducer(request, pk):
    """حذف معرف"""
    introducer = get_object_or_404(PersonalVoterRecord, pk=pk)
    name = introducer.full_name
    introducer.delete()
    messages.success(request, f'تم حذف المعرف: {name}')
    return redirect('personal_voter_record')


@login_required
def add_voter_to_introducer(request, introducer_pk):
    """إضافة ناخب للمعرف عبر AJAX"""
    if request.method == 'POST':
        introducer = get_object_or_404(PersonalVoterRecord, pk=introducer_pk)
        voter_number = request.POST.get('voter_number', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        
        if not voter_number:
            return JsonResponse({'success': False, 'error': 'رقم الناخب مطلوب'})
        
        # التحقق من عدم الإضافة مسبقاً
        if IntroducerVoter.objects.filter(introducer=introducer, voter_number=voter_number).exists():
            return JsonResponse({'success': False, 'error': 'هذا الناخب مضاف مسبقاً لهذا المعرف'})
        
        # جلب بيانات الناخب
        voter_data = fetch_voter_from_legacy_db(voter_number)
        
        if not voter_data:
            return JsonResponse({'success': False, 'error': 'رقم الناخب غير موجود في قاعدة البيانات'})
        
        # إضافة الناخب
        voter = IntroducerVoter.objects.create(
            introducer=introducer,
            voter_number=voter_number,
            phone_number=phone_number,
            full_name=voter_data.get('full_name', ''),
            voting_center_name=voter_data.get('voting_center_name', ''),
            voting_center_number=voter_data.get('voting_center_number', ''),
            registration_center_name=voter_data.get('registration_center_name', ''),
            registration_center_number=voter_data.get('registration_center_number', ''),
            station_number=voter_data.get('station_number', ''),
            family_number=voter_data.get('family_number', ''),
            governorate=voter_data.get('governorate', 'البصرة'),
        )
        
        return JsonResponse({
            'success': True,
            'message': 'تمت إضافة الناخب بنجاح',
            'voter': {
                'id': voter.id,
                'full_name': voter.full_name,
                'voter_number': voter.voter_number,
                'phone_number': voter.phone_number,
                'classification': voter.get_classification_display(),
            }
        })
    
    return JsonResponse({'success': False, 'error': 'طريقة الطلب غير صحيحة'})


@login_required
def delete_introducer_voter(request, pk):
    """حذف ناخب من قائمة المعرف"""
    voter = get_object_or_404(IntroducerVoter, pk=pk)
    introducer_pk = voter.introducer.pk
    name = voter.full_name
    voter.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'تم حذف {name}'})
    
    messages.success(request, f'تم حذف {name}')
    return redirect('introducer_detail', pk=introducer_pk)


@login_required
def update_voter_classification(request, pk):
    """تحديث تصنيف الناخب"""
    if request.method == 'POST':
        voter = get_object_or_404(IntroducerVoter, pk=pk)
        classification = request.POST.get('classification', 'supporter')
        voter.classification = classification
        voter.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'تم تحديث التصنيف',
            'classification': voter.get_classification_display()
        })
    
    return JsonResponse({'success': False, 'error': 'طريقة الطلب غير صحيحة'})


# Legacy compatibility functions
add_voter_to_personal_record = add_voter_to_introducer
delete_personal_voter_record = delete_introducer



# ==================== Observer Registration Views (تسجيل المراقبين) ====================
# Based on Video 3: 17-05-27.mp4

class ObserverRegistrationListView(LoginRequiredMixin, ListView):
    """عرض قائمة المراقبين المسجلين"""
    model = ObserverRegistration
    template_name = 'elections/observer_registration_list.html'
    context_object_name = 'observers'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = ObserverRegistration.objects.all()
        
        # Search filter
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(voter_number__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(national_id__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-registered_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['total_count'] = ObserverRegistration.objects.count()
        context['pending_count'] = ObserverRegistration.objects.filter(status='pending').count()
        context['approved_count'] = ObserverRegistration.objects.filter(status='approved').count()
        return context


class ObserverRegistrationCreateView(LoginRequiredMixin, CreateView):
    """تسجيل مراقب أو وكيل جديد"""
    model = ObserverRegistration
    form_class = ObserverRegistrationForm
    template_name = 'elections/observer_registration_form.html'
    success_url = reverse_lazy('observer_registration_list')
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        
        # ربط بالمرشح إذا كان مراقب مرشح
        if instance.observer_type == 'candidate_monitor' and instance.candidate_code:
            # البحث عن المرشح برقم الناخب (كود المرشح)
            candidate = PartyCandidate.objects.filter(voter_number=instance.candidate_code).first()
            if candidate:
                instance.linked_candidate = candidate
            else:
                messages.warning(self.request, 'لم يتم العثور على مرشح بهذا الكود')
        
        instance.save()
        type_label = "المراقب" if instance.observer_type == 'candidate_monitor' else "الوكيل"
        messages.success(self.request, f'تم تسجيل {type_label} بنجاح!')
        return redirect(self.success_url)


class ObserverRegistrationDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل المراقب المسجل"""
    model = ObserverRegistration
    template_name = 'elections/observer_registration_detail.html'
    context_object_name = 'observer'


@login_required
def approve_observer(request, pk):
    """الموافقة على تسجيل المراقب"""
    observer = get_object_or_404(ObserverRegistration, pk=pk)
    observer.status = 'approved'
    observer.approved_at = timezone.now()
    observer.save()
    messages.success(request, f'تم اعتماد تسجيل {observer.full_name}')
    return redirect('observer_registration_list')


@login_required
def reject_observer(request, pk):
    """رفض تسجيل المراقب"""
    observer = get_object_or_404(ObserverRegistration, pk=pk)
    observer.status = 'rejected'
    observer.save()
    messages.warning(request, f'تم رفض تسجيل {observer.full_name}')
    return redirect('observer_registration_list')


@login_required
def save_face_capture(request, pk):
    """حفظ صورة التقاط الوجه"""
    if request.method == 'POST':
        observer = get_object_or_404(ObserverRegistration, pk=pk)
        
        if 'face_capture' in request.FILES:
            observer.face_capture = request.FILES['face_capture']
            observer.face_captured = True
            observer.face_capture_date = timezone.now()
            observer.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم حفظ صورة الوجه بنجاح'
            })
        
        # Handle base64 image data
        image_data = request.POST.get('face_capture_data')
        if image_data:
            import base64
            from django.core.files.base import ContentFile
            
            # Remove header if present
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            
            image_binary = base64.b64decode(image_data)
            file_name = f'face_{observer.voter_number}_{timezone.now().strftime("%Y%m%d%H%M%S")}.jpg'
            observer.face_capture.save(file_name, ContentFile(image_binary), save=False)
            observer.face_captured = True
            observer.face_capture_date = timezone.now()
            observer.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم حفظ صورة الوجه بنجاح'
            })
    
    return JsonResponse({'success': False, 'error': 'فشل في حفظ الصورة'})


# ==================== Helper Functions ====================

def fetch_voter_from_legacy_db(voter_number):
    """
    Search for voter data:
    1. First in the Django Voter model (primary source).
    2. Then in the legacy SQLite DB (fallback).
    """
    # 1. Try Voter Model
    try:
        voter = Voter.objects.filter(voter_number=voter_number).first()
        if voter:
            return {
                'full_name': voter.full_name,
                'voting_center_name': voter.voting_center_name,
                'voting_center_number': voter.voting_center_number,
                'registration_center_name': voter.registration_center_name,
                'registration_center_number': voter.registration_center_number,
                'station_number': voter.station_number,
                'family_number': voter.family_number,
                'governorate': voter.governorate,
            }
    except Exception as e:
        print(f"Error fetching from Voter model: {e}")

    # 2. Try Legacy DB (Fallback)
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'البرنامج الانتخابي', 'prs21_decrypted.db'
    )
    
    if not os.path.exists(db_path):
        # Try alternate path
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'prs21_decrypted.db'
        )
    
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, center_name, center_number, 
                   registration_center_name, registration_center_number,
                   station_number, family_number, governorate
            FROM voters
            WHERE voter_number = ?
        """, (voter_number,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'full_name': row[0] or '',
                'voting_center_name': row[1] or '',
                'voting_center_number': row[2] or '',
                'registration_center_name': row[3] or '',
                'registration_center_number': row[4] or '',
                'station_number': row[5] or '',
                'family_number': row[6] or '',
                'governorate': row[7] or 'البصرة',
            }
    except Exception as e:
        print(f"Error fetching voter from legacy DB: {e}")
    
    return None


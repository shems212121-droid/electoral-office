from django import forms
from .models import (
    Candidate, Anchor, Introducer, Voter, CandidateMonitor, CommunicationLog, CampaignTask,
    PoliticalParty, PartyCandidate, PollingCenter, PollingStation, VoteCount,
    ElectoralPublic, PersonalVoterRecord, IntroducerVoter, ObserverRegistration,
    CenterDirector, PoliticalEntityAgent, Organization
)


# CandidateForm is now an alias to PartyCandidateForm (defined below)


class AnchorForm(forms.ModelForm):
    # حقل اختيار مخصص يدمج المرشحين من كلا النموذجين
    candidate_choice = forms.ChoiceField(
        label='المرشح',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        # Extract candidate_id from kwargs if passed from view
        candidate_id = kwargs.pop('candidate_id', None)
        super(AnchorForm, self).__init__(*args, **kwargs)
        self.fields['voter_number'].required = True
        self.fields['phone'].required = True
        
        # بناء قائمة المرشحين من كلا النموذجين
        from .models import Candidate, PartyCandidate
        
        choices = [('', '---------')]
        
        # إضافة المرشحين من نموذج PartyCandidate الجديد
        party_candidates = PartyCandidate.objects.all().order_by('full_name')
        for pc in party_candidates:
            choices.append((f'pc_{pc.pk}', f'{pc.full_name} ({pc.candidate_code or "جديد"})'))
        
        # إضافة المرشحين من نموذج Candidate القديم (الذين ليس لديهم نظير في PartyCandidate)
        old_candidates = Candidate.objects.all().order_by('full_name')
        for c in old_candidates:
            choices.append((f'c_{c.pk}', f'{c.full_name} ({c.candidate_code or "قديم"})'))
        
        self.fields['candidate_choice'].choices = choices
        
        # تحديد القيمة المبدئية من البيانات الموجودة
        if self.instance and self.instance.pk:
            if self.instance.party_candidate:
                self.fields['candidate_choice'].initial = f'pc_{self.instance.party_candidate.pk}'
            elif self.instance.candidate:
                self.fields['candidate_choice'].initial = f'c_{self.instance.candidate.pk}'
        
        # Pre-select candidate if candidate_id is provided
        if candidate_id:
            try:
                candidate = PartyCandidate.objects.get(pk=candidate_id)
                self.fields['candidate_choice'].initial = f'pc_{candidate.pk}'
            except PartyCandidate.DoesNotExist:
                try:
                    candidate = Candidate.objects.get(pk=candidate_id)
                    self.fields['candidate_choice'].initial = f'c_{candidate.pk}'
                except Candidate.DoesNotExist:
                    pass
    
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # التحقق من عدم تكرار رقم الهاتف (مع استثناء السجل الحالي عند التعديل)
            qs = Anchor.objects.filter(phone=phone)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('رقم الهاتف مسجل مسبقاً كمرتكز. يرجى استخدام رقم آخر.')
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        voter_number = cleaned_data.get('voter_number')
        candidate_choice = cleaned_data.get('candidate_choice')
        
        # معالجة الحقل المخصص candidate_choice
        from .models import Candidate, PartyCandidate
        
        if candidate_choice:
            if candidate_choice.startswith('pc_'):
                # مرشح من نموذج PartyCandidate
                try:
                    pk = int(candidate_choice[3:])
                    party_candidate = PartyCandidate.objects.get(pk=pk)
                    cleaned_data['party_candidate'] = party_candidate
                    cleaned_data['candidate'] = None
                except (ValueError, PartyCandidate.DoesNotExist):
                    self.add_error('candidate_choice', 'المرشح المختار غير موجود')
            elif candidate_choice.startswith('c_'):
                # مرشح من نموذج Candidate القديم
                try:
                    pk = int(candidate_choice[2:])
                    candidate = Candidate.objects.get(pk=pk)
                    cleaned_data['candidate'] = candidate
                    cleaned_data['party_candidate'] = None
                except (ValueError, Candidate.DoesNotExist):
                    self.add_error('candidate_choice', 'المرشح المختار غير موجود')
        else:
            self.add_error('candidate_choice', 'يجب اختيار المرشح')
        
        # التحقق من عدم تسجيل نفس الناخب كمرتكز لنفس المرشح
        party_candidate = cleaned_data.get('party_candidate')
        candidate = cleaned_data.get('candidate')
        
        if voter_number:
            if party_candidate:
                qs = Anchor.objects.filter(voter_number=voter_number, party_candidate=party_candidate)
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    self.add_error('voter_number', 'هذا الناخب مسجل مسبقاً كمرتكز لنفس المرشح.')
            elif candidate:
                qs = Anchor.objects.filter(voter_number=voter_number, candidate=candidate)
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    self.add_error('voter_number', 'هذا الناخب مسجل مسبقاً كمرتكز لنفس المرشح.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # تعيين المرشح من البيانات المنظفة
        if hasattr(self, 'cleaned_data'):
            instance.party_candidate = self.cleaned_data.get('party_candidate')
            instance.candidate = self.cleaned_data.get('candidate')
        if commit:
            instance.save()
        return instance
    
    class Meta:
        model = Anchor
        # رقم الناخب ورقم الهاتف أول حقلين
        # ملاحظة: candidate و party_candidate يتم التعامل معهم في save() method
        fields = ['voter_number', 'phone', 'full_name',
                 'date_of_birth', 'voting_center_number', 'voting_center_name', 'family_number',
                 'registration_center_name', 'registration_center_number',
                 'governorate', 'station_number', 'status']
        widgets = {
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الناخب'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class IntroducerForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        # Extract anchor_id from kwargs if passed from view
        anchor_id = kwargs.pop('anchor_id', None)
        super(IntroducerForm, self).__init__(*args, **kwargs)
        self.fields['voter_number'].required = True
        self.fields['phone'].required = True
        
        # Pre-select anchor if anchor_id is provided
        if anchor_id:
            try:
                from .models import Anchor
                anchor = Anchor.objects.get(pk=anchor_id)
                self.fields['anchor'].initial = anchor
            except Anchor.DoesNotExist:
                pass
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # التحقق من عدم تكرار رقم الهاتف (مع استثناء السجل الحالي عند التعديل)
            qs = Introducer.objects.filter(phone=phone)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('رقم الهاتف مسجل مسبقاً كمعرف. يرجى استخدام رقم آخر.')
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        voter_number = cleaned_data.get('voter_number')
        anchor = cleaned_data.get('anchor')
        
        if voter_number and anchor:
            # التحقق من عدم تسجيل نفس الناخب كمعرف لنفس المرتكز
            qs = Introducer.objects.filter(voter_number=voter_number, anchor=anchor)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('voter_number', 'هذا الناخب مسجل مسبقاً كمعرف لنفس المرتكز.')
        
        return cleaned_data
    
    class Meta:
        model = Introducer
        # رقم الناخب ورقم الهاتف أول حقلين
        fields = ['voter_number', 'phone', 'full_name', 'anchor',
                 'date_of_birth', 'voting_center_number', 'voting_center_name', 'family_number',
                 'registration_center_name', 'registration_center_number',
                 'governorate', 'station_number', 'status']
        widgets = {
            'anchor': forms.Select(attrs={'class': 'form-select'}),
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الناخب'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class VoterAssignmentForm(forms.ModelForm):
    class Meta:
        model = Voter
        fields = ['introducer']
        widgets = {
            'introducer': forms.Select(attrs={'class': 'form-select'}),
        }


class CommunicationLogForm(forms.ModelForm):
    class Meta:
        model = CommunicationLog
        fields = ['phone_number', 'call_status', 'outcome']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'call_status': forms.Select(attrs={'class': 'form-select'}),
            'outcome': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'سجل ملاحظات ونتيجة الاتصال هنا...'}),
        }


class CampaignTaskForm(forms.ModelForm):
    class Meta:
        model = CampaignTask
        fields = ['title', 'description', 'assigned_to', 'target_area', 'priority', 'status', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'assigned_to': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الشخص المكلف'}),
            'target_area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الجهة المستهدفة'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class CandidateMonitorForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        # Extract candidate_id from kwargs if passed from view
        candidate_id = kwargs.pop('candidate_id', None)
        super(CandidateMonitorForm, self).__init__(*args, **kwargs)
        self.fields['voter_number'].required = True
        self.fields['phone'].required = True
        
        # Pre-select candidate if candidate_id is provided
        if candidate_id:
            try:
                from .models import Candidate
                candidate = Candidate.objects.get(pk=candidate_id)
                self.fields['candidate'].initial = candidate
            except Candidate.DoesNotExist:
                pass
    
    class Meta:
        model = CandidateMonitor
        # رقم الناخب ورقم الهاتف أول حقلين
        fields = ['voter_number', 'phone', 'full_name', 'role_type', 'candidate',
                 'mother_name', 'gender', 'date_of_birth',
                 'voting_center_number', 'voting_center_name', 'family_number',
                 'registration_center_name', 'registration_center_number',
                 'governorate', 'station_number',
                 'photo', 'face_capture', 'national_id',
                 'marital_status', 'education',
                 'district', 'sub_district', 'neighborhood_number', 'alley', 'nearest_landmark', 'full_address',
                 'section', 'status']
        widgets = {
            'role_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_role_type'}),
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الناخب'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'face_capture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'capture': 'user'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم البطاقة الوطنية'}),
            'candidate': forms.Select(attrs={'class': 'form-select', 'id': 'id_candidate'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الأم'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'readonly': 'readonly'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'education': forms.Select(attrs={'class': 'form-select'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'القضاء'}),
            'sub_district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الناحية'}),
            'neighborhood_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم المحلة'}),
            'alley': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الزقاق'}),
            'nearest_landmark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أقرب نقطة دالة'}),
            'full_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'voting_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'family_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'station_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'القسم'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        role_type = cleaned_data.get('role_type')
        candidate = cleaned_data.get('candidate')
        
        if role_type == 'candidate_observer' and not candidate:
            self.add_error('candidate', 'يجب اختيار المرشح للمراقب')
            
        return cleaned_data


# ==================== Vote Counting Forms ====================

class PoliticalPartyForm(forms.ModelForm):
    class Meta:
        model = PoliticalParty
        fields = ['name', 'serial_number', 'logo', 'color', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الحزب'}),
            'serial_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الرقم التسلسلي'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PartyCandidateForm(forms.ModelForm):
    """نموذج موحد للمرشحين - يدعم المرشحين الحزبيين والمستقلين"""
    
    def __init__(self, *args, **kwargs):
        super(PartyCandidateForm, self).__init__(*args, **kwargs)
        self.fields['voter_number'].required = True
        self.fields['phone'].required = True
    
    class Meta:
        model = PartyCandidate
        # رقم الناخب ورقم الهاتف أول حقلين
        fields = [
            'voter_number', 'phone', 'party', 'council_type', 'serial_number',
            'full_name', 'date_of_birth', 'voting_center_number', 'voting_center_name',
            'registration_center_number', 'registration_center_name',
            'family_number', 'station_number', 'governorate', 'status',
            'mother_name_triple', 'address', 'photo', 'biography'
        ]
        widgets = {
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الناخب'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'mother_name_triple': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'party': forms.Select(attrs={'class': 'form-select'}),
            'council_type': forms.Select(attrs={'class': 'form-select'}),
            'serial_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الرقم التسلسلي (اختياري)'}),
            'voting_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'family_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'station_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'status': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'biography': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


# Keep CandidateForm as an alias for backward compatibility
CandidateForm = PartyCandidateForm



class PollingCenterForm(forms.ModelForm):
    class Meta:
        model = PollingCenter
        fields = ['name', 'center_number', 'area', 'neighborhood', 'address', 'station_count', 'total_registered_voters']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المركز'}),
            'center_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم المركز'}),
            'area': forms.Select(attrs={'class': 'form-select'}),
            'neighborhood': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'station_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'عدد المحطات'}),
            'total_registered_voters': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'عدد الناخبين'}),
        }


class PollingStationForm(forms.ModelForm):
    class Meta:
        model = PollingStation
        fields = ['center', 'station_number', 'registered_voters', 'total_ballots_received', 
                 'valid_votes', 'invalid_votes', 'counting_status', 'notes']
        widgets = {
            'center': forms.Select(attrs={'class': 'form-select'}),
            'station_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'رقم المحطة'}),
            'registered_voters': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الناخبين المسجلين'}),
            'total_ballots_received': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الأوراق المستلمة'}),
            'valid_votes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الأصوات الصحيحة'}),
            'invalid_votes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الأصوات الباطلة'}),
            'counting_status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class VoteCountForm(forms.ModelForm):
    class Meta:
        model = VoteCount
        fields = ['station', 'candidate', 'vote_count', 'vote_type', 'notes']
        widgets = {
            'station': forms.Select(attrs={'class': 'form-select'}),
            'candidate': forms.Select(attrs={'class': 'form-select'}),
            'vote_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'عدد الأصوات', 'min': '0'}),
            'vote_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'ملاحظات (اختياري)'}),
        }


class GeneralVoteCountForm(forms.ModelForm):
    """نموذج الجرد العام"""
    class Meta:
        model = VoteCount
        fields = ['station', 'candidate', 'vote_count', 'notes']
        widgets = {
            'station': forms.Select(attrs={'class': 'form-select'}),
            'candidate': forms.Select(attrs={'class': 'form-select'}),
            'vote_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'عدد الأصوات', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'ملاحظات (اختياري)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vote_count'].initial = None

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.vote_type = 'general'
        if commit:
            instance.save()
        return instance


class SpecialVoteCountForm(forms.ModelForm):
    """نموذج الجرد الخاص"""
    class Meta:
        model = VoteCount
        fields = ['station', 'candidate', 'vote_count', 'notes']
        widgets = {
            'station': forms.Select(attrs={'class': 'form-select'}),
            'candidate': forms.Select(attrs={'class': 'form-select'}),
            'vote_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'عدد الأصوات', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'ملاحظات (اختياري)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vote_count'].initial = None

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.vote_type = 'special'
        if commit:
            instance.save()
        return instance


class QuickVoteCountForm(forms.Form):
    """نموذج الجرد السريع - لإدخال أصوات جميع المرشحين في محطة واحدة"""
    station = forms.ModelChoiceField(
        queryset=PollingStation.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="المحطة"
    )
    vote_type = forms.ChoiceField(
        choices=VoteCount.VOTE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="نوع التصويت",
        initial='general'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # سيتم إضافة حقول ديناميكية لكل مرشح
        candidates = PartyCandidate.objects.select_related('party').order_by('party__serial_number', 'serial_number')
        for candidate in candidates:
            field_name = f'candidate_{candidate.id}'
            self.fields[field_name] = forms.IntegerField(
                min_value=0,
                required=False,
                initial=None,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control vote-input',
                    'min': '0',
                    'placeholder': ''
                }),
                label=str(candidate)
            )


# ==================== Electoral Public Forms (المرتكزات) ====================

class ElectoralPublicForm(forms.ModelForm):
    """نموذج تسجيل المرتكزات"""
    
    def __init__(self, *args, **kwargs):
        super(ElectoralPublicForm, self).__init__(*args, **kwargs)
        self.fields['voter_number'].required = True
        self.fields['phone_number'].required = True
        self.fields['password'].required = True
        self.fields['candidate'].required = True
    
    class Meta:
        model = ElectoralPublic
        # الحقول بالترتيب المطلوب: رقم الناخب، الهاتف، كلمة المرور، المرشح
        fields = ['voter_number', 'phone_number', 'password', 'candidate',
                 'full_name', 'voting_center_number', 'voting_center_name',
                 'registration_center_name', 'registration_center_number',
                 'station_number', 'governorate', 'status', 'notes']
        widgets = {
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل رقم الناخب', 'dir': 'ltr'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07XXXXXXXXX', 'dir': 'ltr'}),
            'password': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'كلمة المرور'}),
            'candidate': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'station_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# ==================== Personal Voter Record Forms (المعرفين) ====================

class PersonalVoterRecordForm(forms.ModelForm):
    """نموذج إضافة معرف جديد"""
    
    def __init__(self, *args, **kwargs):
        super(PersonalVoterRecordForm, self).__init__(*args, **kwargs)
        self.fields['voter_number'].required = True
        self.fields['phone_number'].required = True
        self.fields['anchor_code'].required = True
    
    class Meta:
        model = PersonalVoterRecord
        # رقم الناخب، الهاتف، كود المرتكز
        fields = ['voter_number', 'phone_number', 'anchor_code',
                 'full_name', 'voting_center_number', 'voting_center_name',
                 'registration_center_name', 'registration_center_number',
                 'station_number', 'family_number', 'governorate',
                 'classification', 'notes']
        widgets = {
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل رقم الناخب', 'dir': 'ltr'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف', 'dir': 'ltr'}),
            'anchor_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'كود المرتكز', 'dir': 'ltr'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'station_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'family_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'classification': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class IntroducerVoterForm(forms.ModelForm):
    """نموذج إضافة ناخب للمعرف"""
    
    def __init__(self, *args, **kwargs):
        super(IntroducerVoterForm, self).__init__(*args, **kwargs)
        self.fields['voter_number'].required = True
    
    class Meta:
        from .models import IntroducerVoter
        model = IntroducerVoter
        fields = ['voter_number', 'phone_number', 'full_name',
                 'voting_center_number', 'voting_center_name',
                 'registration_center_name', 'registration_center_number',
                 'station_number', 'family_number', 'governorate',
                 'classification', 'notes']
        widgets = {
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل رقم الناخب', 'dir': 'ltr'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف', 'dir': 'ltr'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'station_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'family_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'classification': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class QuickAddVoterForm(forms.Form):
    """نموذج إضافة سريعة للناخب"""
    voter_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'أدخل رقم الناخب', 'dir': 'ltr', 'autofocus': 'autofocus'}),
        label='رقم الناخب'
    )


# ==================== Observer Registration Forms (تسجيل المراقبين) ====================

class ObserverRegistrationForm(forms.ModelForm):
    """نموذج تسجيل المراقبين والوكلاء الموحد"""
    
    def __init__(self, *args, **kwargs):
        super(ObserverRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['voter_number'].required = True
        self.fields['phone_number'].required = True
        self.fields['observer_type'].required = True
    
    class Meta:
        model = ObserverRegistration
        # النوع، رقم الناخب، رقم الهاتف، كود المرشح (للمراقبين)
        fields = ['observer_type', 'voter_number', 'phone_number', 'candidate_code',
                 'full_name', 'mother_name', 'date_of_birth', 'gender',
                 'voting_center_name', 'voting_center_number', 'registration_center_name', 
                 'registration_center_number', 'station_number', 'governorate',
                 'marital_status', 'education', 'national_id',
                 'photo', 'photo_submitted', 'voter_card_submitted', 'national_id_submitted',
                 'password']
        widgets = {
            'observer_type': forms.Select(attrs={'class': 'form-select'}),
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الناخب', 'dir': 'ltr'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07XXXXXXXXX', 'dir': 'ltr'}),
            'candidate_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'كود المرشح (للمراقبين فقط)', 'dir': 'ltr'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'education': forms.Select(attrs={'class': 'form-select'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voting_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'registration_center_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'station_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'photo_submitted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'voter_card_submitted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'national_id_submitted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'كلمة المرور'}),
        }


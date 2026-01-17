from django import forms
from .models import CenterDirector, PoliticalEntityAgent, SubOperationRoom

# ==================== Center Directors and Political Entity Agents Forms ====================

class CenterDirectorForm(forms.ModelForm):
    """نموذج مدراء المراكز الانتخابية"""
    
    def __init__(self, *args, **kwargs):
        super(CenterDirectorForm, self).__init__(*args, **kwargs)
        # رقم الهاتف إجباري، لكن رقم الناخب اختياري
        self.fields['phone'].required = True
        self.fields['voter_number'].required = False  # اختياري لأن المدير قد لا يكون ناخباً
        if not self.instance.pk:
            self.fields['governorate'].initial = 'البصرة'
        # الترتيب: جعل القائمة المنسدلة للغرف واضحة
        self.fields['sub_room'].queryset = SubOperationRoom.objects.filter(is_active=True)
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # التحقق من عدم تكرار رقم الهاتف (مع استثناء السجل الحالي عند التعديل)
            qs = CenterDirector.objects.filter(phone=phone)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('رقم الهاتف مسجل مسبقاً لمدير مركز آخر. يرجى استخدام رقم آخر.')
        return phone
    
    def clean_assigned_center_number(self):
        center_number = self.cleaned_data.get('assigned_center_number')
        if center_number:
            # التحقق من عدم تكرار رقم المركز (مع استثناء السجل الحالي عند التعديل)
            qs = CenterDirector.objects.filter(assigned_center_number=center_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('رقم المركز مسجل مسبقاً. يجب أن يكون لكل مركز مدير واحد فقط.')
        return center_number
    
    class Meta:
        model = CenterDirector
        # رقم الناخب ورقم الهاتف أول حقلين، ثم الغرفة
        fields = ['voter_number', 'phone', 'full_name', 'sub_room',
                 'voting_type', 'assigned_center_number', 'assigned_center_name', 
                 'governorate', 'email', 'national_id', 'status', 'start_date', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الكامل'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07XXXXXXXXX', 'dir': 'ltr'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com', 'dir': 'ltr'}),
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الناخب (اختياري)', 'dir': 'ltr'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم البطاقة الوطنية (اختياري)', 'dir': 'ltr'}),
            'sub_room': forms.Select(attrs={'class': 'form-select'}),
            'voting_type': forms.Select(attrs={'class': 'form-select'}),
            'assigned_center_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم المركز الانتخابي'}),
            'assigned_center_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المركز الانتخابي'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات إضافية..'}),
        }




class PoliticalEntityAgentForm(forms.ModelForm):
    """نموذج وكلاء الكيانات السياسية"""
    
    def __init__(self, *args, **kwargs):
        super(PoliticalEntityAgentForm, self).__init__(*args, **kwargs)
        if 'sub_room' in self.fields:
            self.fields['sub_room'].queryset = SubOperationRoom.objects.filter(is_active=True)

    class Meta:
        model = PoliticalEntityAgent
        # رقم الناخب ورقم الهاتف أول حقلين، ثم الغرفة
        fields = ['voter_number', 'phone', 'full_name', 'sub_room', 'age', 'governorate',
                 'assigned_center_number', 'assigned_center_name', 'assigned_station_number',
                 'political_entity', 'center_director', 'national_id', 'email', 'address',
                 'photo_submitted', 'voter_card_submitted', 'national_id_submitted', 'has_biometric_card',
                 'badge_number', 'badge_issued', 'badge_issue_date',
                 'status', 'verification_date', 'approval_date',
                 'interview_scheduled', 'interview_date', 'interview_completed', 'notes']
        widgets = {
            'sub_room': forms.Select(attrs={'class': 'form-select'}),
            'political_entity': forms.Select(attrs={'class': 'form-select'}),
            'center_director': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الكامل'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'العمر', 'min': '18'}),
            'voter_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الناخب', 'dir': 'ltr'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم البطاقة الوطنية', 'dir': 'ltr'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07XXXXXXXXX', 'dir': 'ltr'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com', 'dir': 'ltr'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العنوان'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_center_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم مركز الاقتراع'}),
            'assigned_center_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم مركز الاقتراع'}),
            'assigned_station_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم المحطة'}),
            'photo_submitted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'voter_card_submitted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'national_id_submitted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_biometric_card': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'badge_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الباج'}),
            'badge_issued': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'badge_issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'verification_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'approval_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'interview_scheduled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'interview_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'interview_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات..'}),
        }


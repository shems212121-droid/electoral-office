from django import forms
from django.contrib.auth.models import User
from .models import SubOperationRoom, Introducer, Anchor, CenterDirector, PoliticalEntityAgent


class SubOperationRoomForm(forms.ModelForm):
    """نموذج إضافة وتعديل غرفة العمليات الفرعية"""
    
    class Meta:
        model = SubOperationRoom
        fields = ['name', 'description', 'supervisor', 'phone', 'location', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الغرفة (مثال: غرفة العمليات الأولى)',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف الغرفة ومهامها...'
            }),
            'supervisor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الموقع أو العنوان'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'اسم الغرفة',
            'description': 'الوصف',
            'supervisor': 'المشرف المسؤول',
            'phone': 'رقم الهاتف',
            'location': 'الموقع',
            'is_active': 'نشط'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter supervisors to only show staff users
        self.fields['supervisor'].queryset = User.objects.filter(is_staff=True).order_by('username')
        self.fields['supervisor'].empty_label = "اختر المشرف (اختياري)"


class SubRoomFilterForm(forms.Form):
    """نموذج تصفية البيانات حسب الغرفة"""
    sub_room = forms.ModelChoiceField(
        queryset=SubOperationRoom.objects.filter(is_active=True).order_by('room_code'),
        required=False,
        empty_label="جميع الغرف",
        label="الغرفة",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'this.form.submit()'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AssignToRoomForm(forms.Form):
    """نموذج تعيين أشخاص لغرفة معينة"""
    sub_room = forms.ModelChoiceField(
        queryset=SubOperationRoom.objects.filter(is_active=True).order_by('room_code'),
        required=True,
        label="الغرفة",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    person_type = forms.ChoiceField(
        choices=[
            ('introducer', 'معرف'),
            ('anchor', 'مرتكز'),
            ('director', 'مدير مركز'),
            ('agent', 'وكيل كيان')
        ],
        required=True,
        label="نوع الشخص",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    person_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
        label="المعرفات"
    )


class IntroducerRoomForm(forms.ModelForm):
    """نموذج تعديل المعرف مع الغرفة"""
    
    class Meta:
        model = Introducer
        fields = ['sub_room']
        widgets = {
            'sub_room': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'sub_room': 'غرفة العمليات'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_room'].queryset = SubOperationRoom.objects.filter(is_active=True).order_by('room_code')
        self.fields['sub_room'].empty_label = "لم يتم التعيين"


class AnchorRoomForm(forms.ModelForm):
    """نموذج تعديل المرتكز مع الغرفة"""
    
    class Meta:
        model = Anchor
        fields = ['sub_room']
        widgets = {
            'sub_room': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'sub_room': 'غرفة العمليات'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_room'].queryset = SubOperationRoom.objects.filter(is_active=True).order_by('room_code')
        self.fields['sub_room'].empty_label = "لم يتم التعيين"


class DirectorRoomForm(forms.ModelForm):
    """نموذج تعديل مدير المركز مع الغرفة"""
    
    class Meta:
        model = CenterDirector
        fields = ['sub_room']
        widgets = {
            'sub_room': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'sub_room': 'غرفة العمليات'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_room'].queryset = SubOperationRoom.objects.filter(is_active=True).order_by('room_code')
        self.fields['sub_room'].empty_label = "لم يتم التعيين"


class AgentRoomForm(forms.ModelForm):
    """نموذج تعديل وكيل الكيان مع الغرفة"""
    
    class Meta:
        model = PoliticalEntityAgent
        fields = ['sub_room']
        widgets = {
            'sub_room': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'sub_room': 'غرفة العمليات'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_room'].queryset = SubOperationRoom.objects.filter(is_active=True).order_by('room_code')
        self.fields['sub_room'].empty_label = "لم يتم التعيين"

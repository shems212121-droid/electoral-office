from django import forms
from .models import Letter, CandidateDocument, FormTemplate, ArchiveFolder, ArchivedDocument


class LetterForm(forms.ModelForm):
    """نموذج إضافة وتعديل الكتب"""
    
    class Meta:
        model = Letter
        fields = [
            'letter_type', 'letter_number', 'letter_date',
            'from_entity', 'to_entity', 'subject', 'description',
            'attachment', 'priority', 'status'
        ]
        widgets = {
            'letter_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'letter_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الكتاب',
                'required': True
            }),
            'letter_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'from_entity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الجهة المرسلة'
            }),
            'to_entity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الجهة المستقبلة'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'موضوع الكتاب',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'تفاصيل إضافية...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class CandidateDocumentForm(forms.ModelForm):
    """نموذج رفع وثائق المرشحين"""
    
    class Meta:
        model = CandidateDocument
        fields = [
            'candidate', 'cv_file', 'personal_photo', 'campaign_photo',
            'id_copy', 'certificate_of_good_conduct',
            'educational_certificates', 'other_documents', 'notes'
        ]
        widgets = {
            'candidate': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'cv_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'personal_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'campaign_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'id_copy': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'certificate_of_good_conduct': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'educational_certificates': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'other_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ملاحظات إضافية...'
            }),
        }


class FormTemplateForm(forms.ModelForm):
    """نموذج إضافة الفورمات الجاهزة"""
    
    class Meta:
        model = FormTemplate
        fields = [
            'title', 'category', 'description',
            'file', 'version', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان النموذج',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف مختصر للنموذج...'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1.0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class ArchiveFolderForm(forms.ModelForm):
    """نموذج إنشاء مجلدات الأرشيف"""
    
    class Meta:
        model = ArchiveFolder
        fields = ['name', 'parent', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المجلد',
                'required': True
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف المجلد...'
            }),
        }


class ArchivedDocumentForm(forms.ModelForm):
    """نموذج أرشفة الوثائق"""
    
    class Meta:
        model = ArchivedDocument
        fields = [
            'folder', 'title', 'document_type',
            'document_number', 'document_date',
            'description', 'file', 'tags'
        ]
        widgets = {
            'folder': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان الوثيقة',
                'required': True
            }),
            'document_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نوع الوثيقة'
            }),
            'document_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الوثيقة'
            }),
            'document_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'وصف الوثيقة...'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'كلمات مفتاحية مفصولة بفاصلة'
            }),
        }


class LetterSearchForm(forms.Form):
    """نموذج البحث في الكتب"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'بحث برقم الكتاب، الموضوع، الجهة...'
        })
    )
    
    letter_type = forms.ChoiceField(
        required=False,
        choices=[('', 'الكل')] + list(Letter._meta.get_field('letter_type').choices),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'الكل')] + list(Letter._meta.get_field('priority').choices),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'الكل')] + list(Letter._meta.get_field('status').choices),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


from .models import CandidateInfoForm, CandidateInterview

class CandidateInfoFormForm(forms.ModelForm):
    """نموذج استمارة معلومات المرشحين"""
    class Meta:
        model = CandidateInfoForm
        fields = '__all__'
        widgets = {
            'ticket_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'voter_id': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'grandfather4_name': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            
            'mother_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_grandfather_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_surname': forms.TextInput(attrs={'class': 'form-control'}),
            
            'birth_place': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            
            'governorate': forms.TextInput(attrs={'class': 'form-control'}),
            'qada': forms.TextInput(attrs={'class': 'form-control'}),
            'nahia': forms.TextInput(attrs={'class': 'form-control'}),
            'mahalla': forms.TextInput(attrs={'class': 'form-control'}),
            'zukak': forms.TextInput(attrs={'class': 'form-control'}),
            'dar': forms.TextInput(attrs={'class': 'form-control'}),
            
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            
            'education_level': forms.TextInput(attrs={'class': 'form-control'}),
            'cert_number': forms.TextInput(attrs={'class': 'form-control'}),
            'cert_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cert_issuer': forms.TextInput(attrs={'class': 'form-control'}),
            
            'national_id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ballot_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CandidateInterviewForm(forms.ModelForm):
    """نموذج استمارة المقابلة"""
    class Meta:
        model = CandidateInterview
        fields = '__all__'
        widgets = {
            'candidate_name': forms.TextInput(attrs={'class': 'form-control'}),
            'interview_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'interviewer': forms.TextInput(attrs={'class': 'form-control'}),
            
            'appearance_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            'charisma_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            'speaking_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            
            'cultural_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            'political_awareness': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            'community_influence': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            
            'loyalty_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            'financial_capability': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            
            'strength_points': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'weakness_points': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'general_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

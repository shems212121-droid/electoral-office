from django.db import models
from django.utils import timezone
from elections.models import Candidate, PartyCandidate
from elections.validators import validate_phone_number, validate_voter_number_required
import os


class LetterType(models.TextChoices):
    """أنواع الكتب"""
    INCOMING = 'incoming', 'وارد'
    OUTGOING = 'outgoing', 'صادر'


class Letter(models.Model):
    """نموذج الكتب الواردة والصادرة"""
    
    letter_type = models.CharField(
        max_length=20,
        choices=LetterType.choices,
        verbose_name='نوع الكتاب'
    )
    letter_number = models.CharField(
        max_length=100,
        verbose_name='رقم الكتاب',
        unique=True
    )
    letter_date = models.DateField(
        verbose_name='تاريخ الكتاب',
        default=timezone.now
    )
    
    # جهة الاتصال
    from_entity = models.CharField(
        max_length=300,
        verbose_name='الجهة المرسلة' if LetterType.INCOMING else 'من',
        blank=True
    )
    to_entity = models.CharField(
        max_length=300,
        verbose_name='الجهة المستقبلة' if LetterType.OUTGOING else 'إلى',
        blank=True
    )
    
    # التفاصيل
    subject = models.CharField(
        max_length=500,
        verbose_name='الموضوع'
    )
    description = models.TextField(
        verbose_name='التفاصيل/الملاحظات',
        blank=True
    )
    
    # الملفات المرفقة
    attachment = models.FileField(
        upload_to='letters/%Y/%m/',
        verbose_name='المرفقات',
        blank=True,
        null=True,
        help_text='PDF, Word, صور'
    )
    
    # معلومات إضافية
    priority = models.CharField(
        max_length=20,
        choices=[
            ('normal', 'عادي'),
            ('important', 'مهم'),
            ('urgent', 'عاجل'),
            ('very_urgent', 'عاجل جداً')
        ],
        default='normal',
        verbose_name='الأولوية'
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'قيد الانتظار'),
            ('in_progress', 'قيد المعالجة'),
            ('completed', 'مكتمل'),
            ('archived', 'مؤرشف')
        ],
        default='pending',
        verbose_name='الحالة'
    )
    
    # التتبع
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    created_by = models.CharField(max_length=100, verbose_name='تم الإنشاء بواسطة', blank=True)
    
    class Meta:
        verbose_name = 'كتاب'
        verbose_name_plural = 'الكتب الواردة والصادرة'
        ordering = ['-letter_date', '-created_at']
        indexes = [
            models.Index(fields=['-letter_date']),
            models.Index(fields=['letter_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_letter_type_display()} - {self.letter_number} - {self.subject}"
    
    @property
    def is_overdue(self):
        """تحقق إذا كان الكتاب متأخر في المعالجة"""
        if self.status in ['completed', 'archived']:
            return False
        days_passed = (timezone.now().date() - self.letter_date).days
        if self.priority == 'very_urgent':
            return days_passed > 1
        elif self.priority == 'urgent':
            return days_passed > 3
        elif self.priority == 'important':
            return days_passed > 7
        return days_passed > 14


class CandidateDocument(models.Model):
    """سي في ووثائق المرشحين"""
    
    candidate = models.ForeignKey(
        PartyCandidate,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='المرشح'
    )
    
    # السيرة الذاتية
    cv_file = models.FileField(
        upload_to='candidates/cv/%Y/',
        verbose_name='السيرة الذاتية (CV)',
        blank=True,
        null=True,
        help_text='PDF أو Word'
    )
    
    # الصور
    personal_photo = models.ImageField(
        upload_to='candidates/photos/',
        verbose_name='الصورة الشخصية',
        blank=True,
        null=True
    )
    
    campaign_photo = models.ImageField(
        upload_to='candidates/campaign/',
        verbose_name='صورة الحملة الانتخابية',
        blank=True,
        null=True
    )
    
    # وثائق إضافية
    id_copy = models.FileField(
        upload_to='candidates/documents/id/',
        verbose_name='نسخة الهوية',
        blank=True,
        null=True
    )
    
    certificate_of_good_conduct = models.FileField(
        upload_to='candidates/documents/conduct/',
        verbose_name='شهادة حسن السيرة والسلوك',
        blank=True,
        null=True
    )
    
    educational_certificates = models.FileField(
        upload_to='candidates/documents/education/',
        verbose_name='الشهادات الدراسية',
        blank=True,
        null=True
    )
    
    other_documents = models.FileField(
        upload_to='candidates/documents/other/',
        verbose_name='وثائق أخرى',
        blank=True,
        null=True
    )
    
    # معلومات إضافية
    notes = models.TextField(
        verbose_name='ملاحظات',
        blank=True
    )
    
    # التتبع
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'وثيقة مرشح'
        verbose_name_plural = 'وثائق المرشحين'
        ordering = ['candidate__full_name']
    
    def __str__(self):
        return f"وثائق {self.candidate.full_name}"

    @property
    def completion_percentage(self):
        """حساب نسبة اكتمال الوثائق"""
        fields = [
            self.cv_file, self.personal_photo, self.campaign_photo,
            self.id_copy, self.certificate_of_good_conduct,
            self.educational_certificates, self.other_documents
        ]
        available = sum(1 for f in fields if f)
        return int((available / 7) * 100)

    @property
    def available_count(self):
        """عدد الوثائق المتوفرة"""
        fields = [
            self.cv_file, self.personal_photo, self.campaign_photo,
            self.id_copy, self.certificate_of_good_conduct,
            self.educational_certificates, self.other_documents
        ]
        return sum(1 for f in fields if f)


class FormTemplate(models.Model):
    """الفورمات والنماذج الجاهزة"""
    
    CATEGORY_CHOICES = [
        ('official_letters', 'كتب رسمية'),
        ('reports', 'تقارير'),
        ('forms', 'استمارات'),
        ('certificates', 'شهادات'),
        ('agreements', 'اتفاقيات وعقود'),
        ('requests', 'طلبات'),
        ('notifications', 'تعاميم وإشعارات'),
        ('financial', 'نماذج مالية'),
        ('other', 'أخرى')
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان النموذج'
    )
    
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name='التصنيف'
    )
    
    description = models.TextField(
        verbose_name='الوصف',
        blank=True
    )
    
    # الملف
    file = models.FileField(
        upload_to='templates/forms/',
        verbose_name='الملف'
    )
    
    file_type = models.CharField(
        max_length=20,
        verbose_name='نوع الملف',
        editable=False
    )
    
    # معلومات إضافية
    version = models.CharField(
        max_length=20,
        verbose_name='الإصدار',
        default='1.0'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    download_count = models.IntegerField(
        default=0,
        verbose_name='عدد مرات التحميل'
    )
    
    # التتبع
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'نموذج جاهز'
        verbose_name_plural = 'النماذج والفورمات الجاهزة'
        ordering = ['category', 'title']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"
    
    def save(self, *args, **kwargs):
        """حفظ نوع الملف تلقائياً"""
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            self.file_type = ext
        super().save(*args, **kwargs)
    
    def increment_download(self):
        """زيادة عداد التحميل"""
        self.download_count += 1
        self.save(update_fields=['download_count'])


class ArchiveFolder(models.Model):
    """مجلدات الأرشفة"""
    
    name = models.CharField(
        max_length=200,
        verbose_name='اسم المجلد'
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders',
        verbose_name='المجلد الأب'
    )
    
    description = models.TextField(
        verbose_name='الوصف',
        blank=True
    )
    
    # التتبع
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'مجلد أرشيف'
        verbose_name_plural = 'مجلدات الأرشيف'
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} / {self.name}"
        return self.name


class ArchivedDocument(models.Model):
    """الوثائق المؤرشفة"""
    
    folder = models.ForeignKey(
        ArchiveFolder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name='المجلد'
    )
    
    title = models.CharField(
        max_length=300,
        verbose_name='العنوان'
    )
    
    document_type = models.CharField(
        max_length=100,
        verbose_name='نوع الوثيقة',
        blank=True
    )
    
    document_number = models.CharField(
        max_length=100,
        verbose_name='رقم الوثيقة',
        blank=True
    )
    
    document_date = models.DateField(
        verbose_name='تاريخ الوثيقة',
        null=True,
        blank=True
    )
    
    description = models.TextField(
        verbose_name='الوصف',
        blank=True
    )
    
    # الملف
    file = models.FileField(
        upload_to='archive/%Y/%m/',
        verbose_name='الملف'
    )
    
    # معلومات إضافية
    tags = models.CharField(
        max_length=500,
        verbose_name='الكلمات المفتاحية',
        blank=True,
        help_text='افصل بين الكلمات بفاصلة'
    )
    
    # التتبع
    archived_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الأرشفة')
    archived_by = models.CharField(max_length=100, verbose_name='أرشفه', blank=True)
    
    class Meta:
        verbose_name = 'وثيقة مؤرشفة'
        verbose_name_plural = 'الوثائق المؤرشفة'
        ordering = ['-archived_at']
        indexes = [
            models.Index(fields=['-archived_at']),
            models.Index(fields=['document_type']),
        ]
    
    def __str__(self):
        return self.title


class CandidateInfoForm(models.Model):
    """استمارة معلومات المرشحين (إحسان منور)"""
    
    GENDER_CHOICES = [
        ('M', 'ذكر'),
        ('F', 'أنثى'),
    ]
    
    # 1. التسلسل
    ticket_order = models.IntegerField(verbose_name='تسلسل المرشح داخل القائمة', null=True, blank=True)
    
    # 2. معلومات أساسية
    voter_id = models.CharField(max_length=20, verbose_name='رقم الناخب',
                                 validators=[validate_voter_number_required])
    full_name = models.CharField(max_length=200, verbose_name='اسم المرشح')
    grandfather4_name = models.CharField(max_length=100, verbose_name='اسم الجد الرابع', blank=True)
    surname = models.CharField(max_length=100, verbose_name='اللقب', blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='الجنس')
    
    # معلومات الأم
    mother_name = models.CharField(max_length=100, verbose_name='اسم الام', blank=True)
    mother_father_name = models.CharField(max_length=100, verbose_name='اسم اب الام', blank=True)
    mother_grandfather_name = models.CharField(max_length=100, verbose_name='اسم جد الام', blank=True)
    mother_surname = models.CharField(max_length=100, verbose_name='لقب الام', blank=True)
    
    # التولد
    birth_place = models.CharField(max_length=100, verbose_name='محل التولد', blank=True)
    birth_date = models.DateField(verbose_name='تاريخ التولد', null=True, blank=True)
    
    # السكن
    governorate = models.CharField(max_length=100, verbose_name='المحافظة', default='البصرة')
    qada = models.CharField(max_length=100, verbose_name='القضاء', blank=True)
    nahia = models.CharField(max_length=100, verbose_name='الناحية', blank=True)
    mahalla = models.CharField(max_length=50, verbose_name='المحلة', blank=True)
    zukak = models.CharField(max_length=50, verbose_name='الزقاق', blank=True)
    dar = models.CharField(max_length=50, verbose_name='الدار', blank=True)
    
    # الاتصال
    phone_number = models.CharField(max_length=11, verbose_name='رقم الهاتف',
                                    validators=[validate_phone_number])
    email = models.EmailField(verbose_name='البريد الالكتروني', blank=True, null=True)
    
    # التعليم
    education_level = models.CharField(max_length=100, verbose_name='التحصيل الدراسي', blank=True)
    cert_number = models.CharField(max_length=50, verbose_name='رقم وثيقة التخرج', blank=True)
    cert_date = models.DateField(verbose_name='تاريخ إصدار التأييد', null=True, blank=True)
    cert_issuer = models.CharField(max_length=150, verbose_name='جهة الإصدار', blank=True)
    
    # المستمسكات
    national_id_number = models.CharField(max_length=50, verbose_name='رقم البطاقة الموحدة', blank=True)
    national_id_date = models.DateField(verbose_name='تاريخ إصدار البطاقة الموحدة', null=True, blank=True)
    
    # الاقتراع
    ballot_name = models.CharField(max_length=200, verbose_name='الاسم في ورقة الاقتراع', blank=True)
    
    # التتبع
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'استمارة معلومات مرشح'
        verbose_name_plural = 'استمارات معلومات المرشحين'
        ordering = ['ticket_order', 'full_name']

    def __str__(self):
        return self.full_name


class CandidateInterview(models.Model):
    """استمارة مقابلة المرشحين"""
    
    candidate_name = models.CharField(max_length=200, verbose_name='اسم المرشح')
    interview_date = models.DateField(default=timezone.now, verbose_name='تاريخ المقابلة')
    interviewer = models.CharField(max_length=150, verbose_name='القائم بالمقابلة')
    
    # التقييم الشخصي
    appearance_score = models.IntegerField(verbose_name='المظهر العام (10)', default=0)
    charisma_score = models.IntegerField(verbose_name='الكاريزما والحضور (10)', default=0)
    speaking_score = models.IntegerField(verbose_name='اللباقة والقدرة على التحدث (10)', default=0)
    
    # التقييم الثقافي والسياسي
    cultural_score = models.IntegerField(verbose_name='المستوى الثقافي (10)', default=0)
    political_awareness = models.IntegerField(verbose_name='الوعي السياسي (10)', default=0)
    community_influence = models.IntegerField(verbose_name='التأثير الاجتماعي (10)', default=0)
    
    # التقييم العام
    loyalty_score = models.IntegerField(verbose_name='الولاء والالتزام (10)', default=0)
    financial_capability = models.IntegerField(verbose_name='المقدرة المالية للدعاية (10)', default=0)
    
    # الملاحظات والقرار
    strength_points = models.TextField(verbose_name='نقاط القوة', blank=True)
    weakness_points = models.TextField(verbose_name='نقاط الضعف', blank=True)
    general_notes = models.TextField(verbose_name='ملاحظات عامة', blank=True)
    
    STATUS_CHOICES = [
        ('pending', 'قيد الدراسة'),
        ('accepted', 'مقبول أولياً'),
        ('rejected', 'مرفوض'),
        ('reserve', 'احتياط'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='القرار النهائي')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'استمارة مقابلة'
        verbose_name_plural = 'استمارات المقابلات'
        ordering = ['-interview_date']

    def __str__(self):
        return f"مقابلة: {self.candidate_name}"

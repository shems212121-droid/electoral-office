from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from .validators import validate_phone_number, validate_voter_number_required

# ==================== User Profile and Roles ====================

class UserRole(models.TextChoices):
    """أدوار المستخدمين في النظام"""
    ADMIN = 'admin', 'مدير النظام'
    SUPERVISOR = 'supervisor', 'مشرف'
    DATA_ENTRY_VOTERS = 'data_entry_voters', 'مدخل بيانات الناخبين'
    DATA_ENTRY_CANDIDATES = 'data_entry_candidates', 'مدخل بيانات المرشحين'
    DATA_ENTRY_MONITORS = 'data_entry_monitors', 'مدخل بيانات المراقبين'
    DATA_ENTRY_ANCHORS = 'data_entry_anchors', 'مدخل بيانات المرتكزات'
    DATA_ENTRY_INTRODUCERS = 'data_entry_introducers', 'مدخل بيانات المعرفين'
    DATA_ENTRY_RESULTS = 'data_entry_results', 'مدخل نتائج الانتخابات'
    VIEWER = 'viewer', 'مستعرض فقط'
    CANDIDATE = 'candidate', 'مرشح'
    TECHNICAL_SUPPORT = 'technical_support', 'دعم فني'
    OPERATIONS_ROOM = 'operations_room', 'غرفة عمليات'


class UserProfile(models.Model):
    """ملف تعريف المستخدم مع الأدوار والصلاحيات"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', 
                                verbose_name="المستخدم")
    role = models.CharField(max_length=30, choices=UserRole.choices, default=UserRole.VIEWER,
                           verbose_name="الدور الوظيفي")
    
    # Geographical Assignment
    assigned_area = models.ForeignKey('Area', null=True, blank=True, on_delete=models.SET_NULL,
                                     verbose_name="المنطقة المخصصة", 
                                     help_text="تحديد منطقة عمل محددة للمستخدم")
    assigned_neighborhood = models.ForeignKey('Neighborhood', null=True, blank=True, 
                                              on_delete=models.SET_NULL,
                                              verbose_name="الحي المخصص")
    
    # Entity Links
    linked_candidate = models.ForeignKey('Candidate', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="المرشح المرتبط")
    linked_operations_room = models.ForeignKey('SubOperationRoom', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="غرفة العمليات المرتبطة")
    
    # Permissions
    can_export_reports = models.BooleanField(default=False, verbose_name="يمكنه تصدير التقارير")
    can_delete_records = models.BooleanField(default=False, verbose_name="يمكنه حذف السجلات")
    can_view_sensitive_data = models.BooleanField(default=False, 
                                                  verbose_name="يمكنه عرض البيانات الحساسة")
    
    # Contact
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    employee_id = models.CharField(max_length=50, blank=True, verbose_name="الرقم الوظيفي")
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    activation_date = models.DateField(null=True, blank=True, verbose_name="تاريخ التفعيل")
    deactivation_date = models.DateField(null=True, blank=True, verbose_name="تاريخ التعطيل")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ آخر تحديث")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def has_permission(self, permission_name):
        """التحقق من صلاحية محددة"""
        # Admin has all permissions
        if self.role == UserRole.ADMIN:
            return True
        
        # Supervisor has most permissions except user management
        if self.role == UserRole.SUPERVISOR:
            return permission_name != 'manage_users'
        
        # Specific role permissions
        permission_map = {
            'view_voters': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_VOTERS, UserRole.VIEWER],
            'add_voters': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_VOTERS],
            'edit_voters': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_VOTERS],
            'delete_voters': [UserRole.ADMIN],
            
            'view_candidates': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_CANDIDATES, UserRole.VIEWER],
            'add_candidates': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_CANDIDATES],
            'edit_candidates': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_CANDIDATES],
            'delete_candidates': [UserRole.ADMIN],
            
            'view_anchors': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_ANCHORS, UserRole.VIEWER],
            'add_anchors': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_ANCHORS],
            'edit_anchors': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_ANCHORS],
            
            'view_introducers': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_INTRODUCERS, UserRole.VIEWER],
            'add_introducers': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_INTRODUCERS],
            'edit_introducers': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_INTRODUCERS],
            
            'view_monitors': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_MONITORS, UserRole.VIEWER],
            'add_monitors': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_MONITORS],
            'edit_monitors': [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.DATA_ENTRY_MONITORS],
            
            'export_reports': [UserRole.ADMIN, UserRole.SUPERVISOR],
            'manage_users': [UserRole.ADMIN],
        }
        
        allowed_roles = permission_map.get(permission_name, [])
        return self.role in allowed_roles or self.can_export_reports if permission_name == 'export_reports' else False
    
    def get_dashboard_url(self):
        """الحصول على رابط لوحة التحكم المخصصة للدور"""
        dashboard_map = {
            UserRole.ADMIN: 'admin_dashboard',
            UserRole.SUPERVISOR: 'supervisor_dashboard',
            UserRole.DATA_ENTRY_VOTERS: 'data_entry_dashboard',
            UserRole.DATA_ENTRY_CANDIDATES: 'data_entry_dashboard',
            UserRole.DATA_ENTRY_MONITORS: 'data_entry_dashboard',
            UserRole.DATA_ENTRY_ANCHORS: 'data_entry_dashboard',
            UserRole.DATA_ENTRY_INTRODUCERS: 'data_entry_dashboard',
            UserRole.VIEWER: 'viewer_dashboard',
            UserRole.CANDIDATE: 'candidates_dashboard',
            UserRole.TECHNICAL_SUPPORT: 'tech_support_dashboard',
            UserRole.OPERATIONS_ROOM: 'operations_room_dashboard',
        }
        return dashboard_map.get(self.role, 'dashboard')
    
    class Meta:
        verbose_name = "ملف المستخدم"
        verbose_name_plural = "ملفات المستخدمين"
        ordering = ['user__username']


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """إنشاء ملف تعريف تلقائياً عند إنشاء مستخدم جديد"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """حفظ ملف التعريف تلقائياً"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ==================== Lookup Models ====================

class Area(models.Model):
    """النواحي"""
    name = models.CharField(max_length=100, verbose_name="الناحية")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "ناحية"
        verbose_name_plural = "النواحي"
        ordering = ['name']


class Neighborhood(models.Model):
    """الأحياء"""
    name = models.CharField(max_length=100, verbose_name="الحي/المنطقة")
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='neighborhoods', verbose_name="الناحية")
    
    def __str__(self):
        return f"{self.name} - {self.area.name}"
    
    class Meta:
        verbose_name = "حي"
        verbose_name_plural = "الأحياء"
        ordering = ['area', 'name']


# ==================== Voter Model ====================

class Voter(models.Model):
    """سجل الناخبين"""
    CLASSIFICATION_CHOICES = [
        ('supporter', 'مؤيد'),
        ('neutral', 'محايد'),
        ('opponent', 'معارض'),
        ('unknown', 'غير محدد'),
    ]

    # System Code (Generated when assigned to introducer)
    voter_code = models.CharField(max_length=60, unique=True, editable=False, null=True, blank=True, 
                                  verbose_name="كود الناخب في النظام")
    
    # Relationship to Introducer
    introducer = models.ForeignKey('Introducer', on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='voters', verbose_name="المعرف")
    
    # Basic Info
    voter_number = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="رقم الناخب", 
                                     validators=[validate_voter_number_required])
    full_name = models.CharField(max_length=150, db_index=True, verbose_name="الاسم الكامل")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="تاريخ الميلاد")
    mother_name = models.CharField(max_length=100, blank=True, verbose_name="اسم الأم")
    family_number = models.CharField(max_length=50, blank=True, verbose_name="رقم العائلة")
    
    # Contact
    phone = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                            validators=[validate_phone_number], null=True, blank=True)
    
    # Location
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الناحية")
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.SET_NULL, null=True, blank=True, 
                                     verbose_name="الحي/المنطقة")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    
    # Voting Centers (CharFields for raw import)
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    voting_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز الاقتراع")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")
    status = models.CharField(max_length=50, blank=True, verbose_name="الحالة")
    
    # Relationships (Linking to official models)
    polling_center = models.ForeignKey('PollingCenter', on_delete=models.SET_NULL, 
                                      null=True, blank=True, related_name='voters',
                                      verbose_name="مركز الاقتراع (مرتبط)")
    polling_station = models.ForeignKey('PollingStation', on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='voters_list',
                                       verbose_name="المحطة (مرتبطة)")
    registration_center_fk = models.ForeignKey('RegistrationCenter', on_delete=models.SET_NULL, 
                                             null=True, blank=True, related_name='voters',
                                             verbose_name="مركز التسجيل (مرتبط)")
    
    # Campaign Info
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, default='unknown', 
                                     verbose_name="التصنيف")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate voter code if assigned to introducer
        if self.introducer and not self.voter_code:
            count = Voter.objects.filter(introducer=self.introducer).count() + 1
            self.voter_code = f"{self.introducer.introducer_code}-VOT-{count:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.voter_number})"

    class Meta:
        verbose_name = "ناخب"
        verbose_name_plural = "سجل الناخبين"
        ordering = ['voter_number']


# ==================== Electoral Hierarchy Models ====================

class Candidate(models.Model):
    """المرشحين"""
    # Unique Code (03-0001, 03-0002, etc.)
    candidate_code = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True, 
                                     verbose_name="كود المرشح")
    
    # From Voter DB (Auto-filled)
    voter_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    mother_name_triple = models.CharField(max_length=100, blank=True, verbose_name="اسم الأم ثلاثي")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="تاريخ الميلاد")
    
    # Voting Info
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    voting_center_name = models.CharField(max_length=100, blank=True, verbose_name="اسم مركز الاقتراع")
    family_number = models.CharField(max_length=50, blank=True, verbose_name="الرقم العائلي")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    status = models.CharField(max_length=50, blank=True, verbose_name="الحالة")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")

    # Contact Info
    phone = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                            validators=[validate_phone_number], null=True, blank=True)
    address = models.CharField(max_length=200, blank=True, verbose_name="عنوان السكن")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate candidate code if not exists (03-0001, 03-0002, etc.)
        if not self.candidate_code:
            last_candidate = Candidate.objects.order_by('-id').first()
            if last_candidate and last_candidate.candidate_code:
                try:
                    last_num = int(last_candidate.candidate_code.split('-')[1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            self.candidate_code = f"03-{new_num:04d}"
        super().save(*args, **kwargs)

    def get_anchors_count(self):
        return self.anchors.count()

    def get_introducers_count(self):
        return Introducer.objects.filter(anchor__candidate=self).count()

    def get_voters_count(self):
        return Voter.objects.filter(introducer__anchor__candidate=self).count()

    def get_monitors_count(self):
        return self.monitors.count()

    def __str__(self):
        return f"{self.full_name} ({self.candidate_code})"
    
    class Meta:
        verbose_name = "مرشح"
        verbose_name_plural = "المرشحين"
        ordering = ['-created_at']


class Anchor(models.Model):
    """المرتكزات"""
    # Unique Code (03-0001-ANC-001)
    anchor_code = models.CharField(max_length=30, unique=True, editable=False, null=True, blank=True, 
                                   verbose_name="كود المرتكز")
    
    # Relationship
    candidate = models.ForeignKey('Candidate', on_delete=models.CASCADE, related_name='anchors', 
                                 verbose_name="المرشح")
    
    # From Voter DB (Auto-filled)
    voter_number = models.CharField(max_length=50, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="تاريخ الميلاد")
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    voting_center_name = models.CharField(max_length=100, blank=True, verbose_name="اسم مركز الاقتراع")
    family_number = models.CharField(max_length=50, blank=True, verbose_name="الرقم العائلي")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    governorate = models.CharField(max_length=50, blank=True, verbose_name="المحافظة")
    status = models.CharField(max_length=50, blank=True, verbose_name="الحالة")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")
    
    # Contact
    phone = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                            validators=[validate_phone_number], null=True, blank=True)
    
    # Sub-Operation Room
    sub_room = models.ForeignKey('SubOperationRoom', on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 related_name='anchors',
                                 verbose_name="غرفة العمليات")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate anchor code with room code if assigned
        if not self.anchor_code and self.candidate:
            count = Anchor.objects.filter(candidate=self.candidate).count() + 1
            base_code = f"{self.candidate.candidate_code}-{count:03d}"
            
            # Add room code if sub_room is set
            if self.sub_room:
                self.anchor_code = f"{self.sub_room.room_code}-{base_code}"
            else:
                self.anchor_code = base_code
        super().save(*args, **kwargs)

    def get_introducers_count(self):
        return self.introducers.count()

    def get_voters_count(self):
        return Voter.objects.filter(introducer__anchor=self).count()

    def __str__(self):
        return f"{self.full_name} ({self.anchor_code})"
    
    class Meta:
        verbose_name = "مرتكز"
        verbose_name_plural = "المرتكزات"
        ordering = ['-created_at']


class Introducer(models.Model):
    """المعرفين"""
    # Unique Code (auto-generated with room prefix if assigned)
    introducer_code = models.CharField(max_length=60, unique=True, editable=False, null=True, blank=True, 
                                      verbose_name="كود المعرف")
    
    # Relationship
    anchor = models.ForeignKey(Anchor, on_delete=models.CASCADE, related_name='introducers', 
                              verbose_name="المرتكز")
    
    # From Voter DB (Auto-filled)
    voter_number = models.CharField(max_length=50, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="تاريخ الميلاد")
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    voting_center_name = models.CharField(max_length=100, blank=True, verbose_name="اسم مركز الاقتراع")
    family_number = models.CharField(max_length=50, blank=True, verbose_name="الرقم العائلي")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    governorate = models.CharField(max_length=50, blank=True, verbose_name="المحافظة")
    status = models.CharField(max_length=50, blank=True, verbose_name="الحالة")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")
    
    # Contact
    phone = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                            validators=[validate_phone_number], null=True, blank=True)
    
    # Sub-Operation Room
    sub_room = models.ForeignKey('SubOperationRoom', on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 related_name='introducers',
                                 verbose_name="غرفة العمليات")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate introducer code with room prefix if assigned
        if not self.introducer_code and self.anchor:
            count = Introducer.objects.filter(anchor=self.anchor).count() + 1
            base_code = f"{self.anchor.anchor_code}-{count:03d}"
            
            # Add room code prefix if sub_room is set
            # Note: anchor.anchor_code already contains room code if anchor has sub_room
            # So we use sub_room only if anchor doesn't have one
            if self.sub_room and not self.anchor.sub_room:
                self.introducer_code = f"{self.sub_room.room_code}-{base_code}"
            else:
                self.introducer_code = base_code
        super().save(*args, **kwargs)

    def get_voters_count(self):
        return self.voters.count()

    def __str__(self):
        return f"{self.full_name} ({self.introducer_code})"
    
    class Meta:
        verbose_name = "معرف (انتخابي)"
        verbose_name_plural = "المعرفين (انتخابي)"
        ordering = ['-created_at']


class CandidateMonitor(models.Model):
    """مراقبي/وكلاء المرشحين"""
    STATUS_CHOICES = [
        ('present', 'حاضر'),
        ('left', 'انصرف'),
        ('absent', 'غير حاضر'),
    ]
    
    ROLE_CHOICES = [
        ('candidate_observer', 'مراقب مرشح'),
        ('entity_agent', 'وكيل كيان (مراقب حركة)'),
    ]

    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate_observer', verbose_name="نوع الدور")
    
    # Relationship
    candidate = models.ForeignKey('Candidate', on_delete=models.CASCADE, related_name='monitors', 
                                 null=True, blank=True, verbose_name="المرشح")
    
    # From Voter DB (Auto-filled)
    voter_number = models.CharField(max_length=50, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="تاريخ الميلاد")
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    voting_center_name = models.CharField(max_length=100, blank=True, verbose_name="اسم مركز الاقتراع")
    family_number = models.CharField(max_length=50, blank=True, verbose_name="الرقم العائلي")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    governorate = models.CharField(max_length=50, blank=True, verbose_name="المحافظة")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")
    
    # Contact & Status
    phone = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                            validators=[validate_phone_number], null=True, blank=True)
    email = models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    
    # Personal Info & Address
    mother_name = models.CharField(max_length=100, blank=True, verbose_name="اسم الأم")
    gender = models.CharField(max_length=10, choices=[('male', 'ذكر'), ('female', 'أنثى')], default='male', verbose_name="الجنس")
    marital_status = models.CharField(max_length=20, choices=[('single', 'أعزب/عزباء'), ('married', 'متزوج/ة'), ('divorced', 'مطلق/ة'), ('widowed', 'أرمل/ة')], default='single', verbose_name="الحالة الاجتماعية")
    education = models.CharField(max_length=20, choices=[('primary', 'ابتدائي'), ('intermediate', 'متوسط'), ('secondary', 'إعدادي'), ('diploma', 'دبلوم'), ('bachelors', 'بكالوريوس'), ('masters', 'ماجستير'), ('doctorate', 'دكتوراه'), ('other', 'أخرى')], default='secondary', verbose_name="التحصيل الدراسي")
    national_id = models.CharField(max_length=50, blank=True, verbose_name="رقم البطاقة الوطنية")
    
    # Address Details
    district = models.CharField(max_length=100, blank=True, verbose_name="القضاء")
    sub_district = models.CharField(max_length=100, blank=True, verbose_name="الناحية")
    neighborhood_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحلة")
    alley = models.CharField(max_length=100, blank=True, verbose_name="الزقاق")
    nearest_landmark = models.CharField(max_length=200, blank=True, verbose_name="أقرب نقطة دالة")
    full_address = models.TextField(blank=True, verbose_name="العنوان الكامل")
    
    # Images
    photo = models.ImageField(upload_to='monitor_photos/', null=True, blank=True, verbose_name="الصورة الشخصية")
    face_capture = models.ImageField(upload_to='monitor_face_captures/', null=True, blank=True, verbose_name="صورة التحقق الحيوي")
    
    section = models.CharField(max_length=100, blank=True, verbose_name="القسم")
    
    # Badge Information
    badge_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="رقم الباج")
    badge_issued = models.BooleanField(default=False, verbose_name="تم إصدار الباج")
    badge_issue_date = models.DateField(null=True, blank=True, verbose_name="تاريخ إصدار الباج")
    
    # Documents
    has_national_id = models.BooleanField(default=False, verbose_name="يحمل البطاقة الوطنية الموحدة")
    has_biometric_card = models.BooleanField(default=False, verbose_name="يحمل البطاقة البايومترية")
    photo_submitted = models.BooleanField(default=False, verbose_name="تم تقديم الصورة الشخصية")
    
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                verbose_name="مضاف من قبل")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent', verbose_name="الحالة")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.candidate:
            return f"{self.full_name} - {self.get_role_type_display()} - {self.candidate.full_name}"
        return f"{self.full_name} - {self.get_role_type_display()}"
    
    class Meta:
        verbose_name = "مراقب/وكيل مرشح"
        verbose_name_plural = "مراقبي/وكلاء المرشحين"
        ordering = ['-created_at']


# ==================== Observer and Agent Models ====================

class Organization(models.Model):
    """المنظمات (محلية ودولية)"""
    TYPE_CHOICES = [
        ('civil_society', 'منظمة مجتمع مدني محلية'),
        ('international', 'منظمة دولية'),
        ('political_entity', 'كيان سياسي'),
    ]
    
    name = models.CharField(max_length=200, unique=True, verbose_name="اسم المنظمة")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="نوع المنظمة")
    registration_number = models.CharField(max_length=100, blank=True, verbose_name="رقم التسجيل")
    email = models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, verbose_name="العنوان")
    
    # For Political Entities
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, 
                                        verbose_name="مبلغ الإيداع (دينار عراقي)")
    deposit_paid = models.BooleanField(default=False, verbose_name="تم دفع الإيداع")
    
    # Registration Info
    registration_date = models.DateField(null=True, blank=True, verbose_name="تاريخ التسجيل")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        verbose_name = "منظمة"
        verbose_name_plural = "المنظمات"
        ordering = ['name']


class CivilSocietyObserver(models.Model):
    """مراقبو منظمات المجتمع المدني المحلية"""
    STATUS_CHOICES = [
        ('registered', 'مسجل'),
        ('approved', 'معتمد'),
        ('badge_issued', 'تم إصدار الباج'),
        ('rejected', 'مرفوض'),
    ]
    
    # Organization
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, 
                                    related_name='civil_observers',
                                    limit_choices_to={'type': 'civil_society'},
                                    verbose_name="المنظمة")
    
    # Personal Info (شروط المفوضية)
    full_name = models.CharField(max_length=150, verbose_name="الاسم الرباعي")
    age = models.IntegerField(verbose_name="العمر")
    voter_number = models.CharField(max_length=50, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    national_id = models.CharField(max_length=50, blank=True, verbose_name="رقم البطاقة الوطنية")
    
    # Contact
    phone = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                            validators=[validate_phone_number], null=True, blank=True)
    email = models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    address = models.CharField(max_length=200, blank=True, verbose_name="العنوان")
    
    # Assigned Center
    monitoring_center_number = models.CharField(max_length=50, verbose_name="رقم مركز الاقتراع للمراقبة")
    monitoring_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز الاقتراع")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    
    # Documents (شروط المفوضية: صورة شخصية، بطاقة الناخب، البطاقة الوطنية)
    photo_submitted = models.BooleanField(default=False, verbose_name="تم تقديم الصورة الشخصية")
    voter_card_submitted = models.BooleanField(default=False, verbose_name="تم تقديم بطاقة الناخب")
    national_id_submitted = models.BooleanField(default=False, verbose_name="تم تقديم البطاقة الوطنية")
    has_biometric_card = models.BooleanField(default=False, verbose_name="يحمل البطاقة البايومترية")
    
    # Badge
    badge_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="رقم الباج")
    badge_issued = models.BooleanField(default=False, verbose_name="تم إصدار الباج")
    badge_issue_date = models.DateField(null=True, blank=True, verbose_name="تاريخ إصدار الباج")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered', verbose_name="الحالة")
    registration_date = models.DateField(auto_now_add=True, verbose_name="تاريخ التسجيل")
    approval_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الموافقة")
    
    # System
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                verbose_name="مضاف من قبل")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.organization.name}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # شرط العمر: لا يقل عن 18 سنة
        if self.age < 18:
            raise ValidationError({'age': 'يجب ألا يقل العمر عن 18 سنة'})
    
    class Meta:
        verbose_name = "مراقب منظمة مجتمع مدني"
        verbose_name_plural = "مراقبو منظمات المجتمع المدني"
        ordering = ['-created_at']


class InternationalObserver(models.Model):
    """المراقبون الدوليون"""
    STATUS_CHOICES = [
        ('registered', 'مسجل'),
        ('approved', 'معتمد'),
        ('badge_issued', 'تم إصدار الباج'),
        ('rejected', 'مرفوض'),
    ]
    
    # Organization/Embassy
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, 
                                    related_name='international_observers',
                                    limit_choices_to={'type': 'international'},
                                    verbose_name="المنظمة/السفارة")
    
    # Personal Info
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    nationality = models.CharField(max_length=50, verbose_name="الجنسية")
    passport_number = models.CharField(max_length=50, verbose_name="رقم جواز السفر")
    
    # Contact
    phone = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                            validators=[validate_phone_number], null=True, blank=True)
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    
    # Assigned Areas
    monitoring_governorate = models.CharField(max_length=50, blank=True, verbose_name="المحافظة المخصصة للمراقبة")
    monitoring_centers = models.TextField(blank=True, verbose_name="مراكز الاقتراع المخصصة")
    
    # Badge
    badge_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="رقم الباج")
    badge_issued = models.BooleanField(default=False, verbose_name="تم إصدار الباج")
    badge_issue_date = models.DateField(null=True, blank=True, verbose_name="تاريخ إصدار الباج")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered', verbose_name="الحالة")
    registration_date = models.DateField(auto_now_add=True, verbose_name="تاريخ التسجيل")
    approval_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الموافقة")
    
    # System
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                verbose_name="مضاف من قبل")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.organization.name}"
    
    class Meta:
        verbose_name = "مراقب دولي"
        verbose_name_plural = "المراقبون الدوليون"
        ordering = ['-created_at']


class CenterDirector(models.Model):
    """مدراء المراكز الانتخابية"""
    VOTING_TYPE_CHOICES = [
        ('general', 'عام'),
        ('special', 'خاص'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
    ]
    
    # Personal Info
    # Director Code (auto-generated: ROOM-01-DIR-001)
    director_code = models.CharField(max_length=30, unique=True, editable=False,
                                     null=True, blank=True,
                                     verbose_name="كود المدير")
    
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    phone = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                            validators=[validate_phone_number], null=True, blank=True)
    email = models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    voter_number = models.CharField(max_length=50, blank=True, verbose_name="رقم الناخب")
    national_id = models.CharField(max_length=50, blank=True, verbose_name="رقم البطاقة الوطنية")
    
    # Center Assignment
    voting_type = models.CharField(max_length=10, choices=VOTING_TYPE_CHOICES, verbose_name="نوع الاقتراع")
    assigned_center_number = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="رقم المركز الانتخابي")
    assigned_center_name = models.CharField(max_length=200, verbose_name="اسم المركز الانتخابي")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="الحالة")
    start_date = models.DateField(null=True, blank=True, verbose_name="تاريخ بداية المهمة")
    
    # User Account (حساب تسجيل الدخول)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='director_profile',
                                verbose_name="حساب المستخدم")
    
    # System
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='added_directors',
                                verbose_name="مضاف من قبل")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    # Sub-Operation Room
    sub_room = models.ForeignKey('SubOperationRoom', on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 related_name='directors',
                                 verbose_name="غرفة العمليات")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """توليد كود المدير تلقائياً: ROOM-01-DIR-001"""
        if not self.director_code and self.sub_room:
            count = CenterDirector.objects.filter(sub_room=self.sub_room).count() + 1
            self.director_code = f"{self.sub_room.room_code}-DIR-{count:03d}"
        super().save(*args, **kwargs)
    
    def get_agents_count(self):
        """عدد وكلاء الكيان تحت إشراف هذا المدير"""
        return self.agents.count()
    
    def get_stations_with_agents(self):
        """المحطات التي بها وكلاء"""
        return self.agents.values('assigned_station_number').distinct().count()
    
    def __str__(self):
        return f"{self.full_name} - مركز {self.assigned_center_number} ({self.get_voting_type_display()})"
    
    class Meta:
        verbose_name = "مدير مركز انتخابي"
        verbose_name_plural = "مدراء المراكز الانتخابية"
        ordering = ['voting_type', 'assigned_center_number']
        indexes = [
            models.Index(fields=['voting_type', 'assigned_center_number']),
            models.Index(fields=['status']),
        ]


class PoliticalEntityAgent(models.Model):
    """وكلاء الكيانات السياسية"""
    STATUS_CHOICES = [
        ('registered', 'مسجل'),
        ('verified', 'تم التحقق'),
        ('approved', 'معتمد'),
        ('badge_issued', 'تم إصدار الباج'),
        ('rejected', 'مرفوض'),
    ]
    
    # Political Entity
    political_entity = models.ForeignKey(Organization, on_delete=models.CASCADE, 
                                        related_name='agents',
                                        limit_choices_to={'type': 'political_entity'},
                                        verbose_name="الكيان السياسي")
    
    # Center Director (Supervisor)
    center_director = models.ForeignKey('CenterDirector', on_delete=models.SET_NULL, 
                                       null=True, blank=True,
                                       related_name='agents',
                                       verbose_name="مدير المركز")
    
    # Personal Info (شروط المفوضية)
    # Agent Code (auto-generated: ROOM-01-AGT-001)
    agent_code = models.CharField(max_length=30, unique=True, editable=False,
                                  null=True, blank=True,
                                  verbose_name="كود الوكيل")
    
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    age = models.IntegerField(verbose_name="العمر")
    voter_number = models.CharField(max_length=50, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    national_id = models.CharField(max_length=50, blank=True, verbose_name="رقم البطاقة الوطنية")
    
    # Contact
    phone = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                            validators=[validate_phone_number], null=True, blank=True)
    email = models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    address = models.CharField(max_length=200, blank=True, verbose_name="العنوان")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    
    # Assigned Station (مراقب واحد لكل محطة اقتراع)
    assigned_center_number = models.CharField(max_length=50, verbose_name="رقم مركز الاقتراع المخصص")
    assigned_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز الاقتراع")
    assigned_station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة المخصصة")
    
    # Documents (شروط المفوضية)
    photo_submitted = models.BooleanField(default=False, verbose_name="تم تقديم الصورة الشخصية")
    voter_card_submitted = models.BooleanField(default=False, verbose_name="تم تقديم بطاقة الناخب")
    national_id_submitted = models.BooleanField(default=False, verbose_name="تم تقديم البطاقة الوطنية")
    has_biometric_card = models.BooleanField(default=False, verbose_name="يحمل البطاقة البايومترية")
    
    # Badge
    badge_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="رقم الباج")
    badge_issued = models.BooleanField(default=False, verbose_name="تم إصدار الباج")
    badge_issue_date = models.DateField(null=True, blank=True, verbose_name="تاريخ إصدار الباج")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered', verbose_name="الحالة")
    registration_date = models.DateField(auto_now_add=True, verbose_name="تاريخ التسجيل الإلكتروني")
    verification_date = models.DateField(null=True, blank=True, verbose_name="تاريخ التحقق من البيانات")
    approval_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الموافقة")
    
    # Interview
    interview_scheduled = models.BooleanField(default=False, verbose_name="تم تحديد موعد المقابلة")
    interview_date = models.DateField(null=True, blank=True, verbose_name="موعد المقابلة")
    interview_completed = models.BooleanField(default=False, verbose_name="تمت المقابلة")
    
    # System
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                verbose_name="مضاف من قبل")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    # Sub-Operation Room
    sub_room = models.ForeignKey('SubOperationRoom', on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 related_name='agents',
                                 verbose_name="غرفة العمليات")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """توليد كود الوكيل تلقائياً: ROOM-01-AGT-001"""
        if not self.agent_code and self.sub_room:
            count = PoliticalEntityAgent.objects.filter(sub_room=self.sub_room).count() + 1
            self.agent_code = f"{self.sub_room.room_code}-AGT-{count:03d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} - {self.political_entity.name}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # شرط العمر: لا يقل عن 18 سنة
        if self.age < 18:
            raise ValidationError({'age': 'يجب ألا يقل العمر عن 18 سنة حسب شروط المفوضية'})
        
        # شرط الجنسية العراقية (يتم التحقق عبر رقم الناخب والبطاقة الوطنية)
        if not self.voter_number:
            raise ValidationError({'voter_number': 'رقم الناخب مطلوب للتحقق من الجنسية العراقية'})
    
    class Meta:
        verbose_name = "وكيل كيان سياسي"
        verbose_name_plural = "وكلاء الكيانات السياسية"
        ordering = ['-created_at']
        # ضمان عدم تكرار نفس الوكيل في نفس المحطة
        unique_together = [['political_entity', 'assigned_center_number', 'assigned_station_number']]


# ==================== Sub-Operation Rooms ====================

class SubOperationRoom(models.Model):
    """غرفة العمليات الفرعية"""
    # كود الغرفة الفريد (ROOM-01, ROOM-02, etc.)
    room_code = models.CharField(max_length=10, unique=True, editable=False, 
                                 verbose_name="كود الغرفة")
    
    # معلومات أساسية
    name = models.CharField(max_length=150, verbose_name="اسم الغرفة")
    description = models.TextField(blank=True, verbose_name="الوصف")
    
    # المشرف المسؤول
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='supervised_rooms', verbose_name="المشرف")
    
    # معلومات الاتصال
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    location = models.CharField(max_length=200, blank=True, verbose_name="الموقع")
    
    # الحالة
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    
    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    
    def save(self, *args, **kwargs):
        """توليد كود الغرفة تلقائياً (ROOM-01, ROOM-02, etc.)"""
        if not self.room_code:
            last_room = SubOperationRoom.objects.order_by('-id').first()
            if last_room and last_room.room_code:
                try:
                    last_num = int(last_room.room_code.split('-')[1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            self.room_code = f"ROOM-{new_num:02d}"
        super().save(*args, **kwargs)
    
    def get_introducers_count(self):
        """عدد المعرفين في الغرفة"""
        return self.introducers.count()
    
    def get_voters_count(self):
        """عدد الناخبين في الغرفة"""
        return Voter.objects.filter(introducer__sub_room=self).count()
    
    def get_anchors_count(self):
        """عدد المرتكزات في الغرفة"""
        return self.anchors.count()
    
    def get_directors_count(self):
        """عدد مدراء المراكز في الغرفة"""
        return self.directors.count()
    
    def get_agents_count(self):
        """عدد وكلاء الكيان في الغرفة"""
        return self.agents.count()
    
    def get_total_people_count(self):
        """العدد الإجمالي للأشخاص في الغرفة"""
        return (self.get_introducers_count() + 
                self.get_voters_count() + 
                self.get_directors_count() + 
                self.get_agents_count())
    
    def __str__(self):
        return f"{self.room_code} - {self.name}"
    
    class Meta:
        verbose_name = "غرفة عمليات فرعية"
        verbose_name_plural = "غرف العمليات الفرعية"
        ordering = ['room_code']


# ==================== Communication & Tasks ====================

# CommunicationLog model has been moved to the end of file and updated to support Generic Relations for the Unified Communication System.


class CampaignTask(models.Model):
    """مهام الحملة الانتخابية"""
    PRIORITY_CHOICES = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
    ]
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'جاري التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]

    title = models.CharField(max_length=200, verbose_name="عنوان المهمة")
    description = models.TextField(verbose_name="وصف المهمة")
    assigned_to = models.CharField(max_length=150, blank=True, verbose_name="المشرف / المكلف")
    target_area = models.CharField(max_length=150, blank=True, verbose_name="الجهة المستهدفة")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="الأولوية")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")
    due_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الاستحقاق")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks', 
                                  verbose_name="أنشئت بواسطة")
    created_at = models.DateTimeField(auto_now_add=True)

    def is_overdue(self):
        """التحقق من تأخر المهمة"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            from datetime import date
            return date.today() > self.due_date
        return False
    
    def days_overdue(self):
        """عدد أيام التأخير"""
        if self.is_overdue():
            from datetime import date
            delta = date.today() - self.due_date
            return delta.days
        return 0

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "مهمة حملة"
        verbose_name_plural = "مهام الحملة"
        ordering = ['-created_at']


# ==================== Vote Counting System ====================

class PoliticalParty(models.Model):
    """الأحزاب السياسية"""
    name = models.CharField(max_length=200, unique=True, verbose_name="اسم الحزب")
    serial_number = models.IntegerField(unique=True, verbose_name="الرقم التسلسلي")
    logo = models.ImageField(upload_to='party_logos/', null=True, blank=True, verbose_name="الشعار")
    color = models.CharField(max_length=7, default='#000000', verbose_name="اللون المميز")
    description = models.TextField(blank=True, verbose_name="الوصف")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_total_votes(self):
        """حساب إجمالي أصوات الحزب"""
        return VoteCount.objects.filter(candidate__party=self).aggregate(
            total=models.Sum('vote_count')
        )['total'] or 0
    
    def get_candidates_count(self):
        """عدد المرشحين"""
        return self.candidates.count()
    
    def __str__(self):
        return f"{self.serial_number} - {self.name}"
    
    class Meta:
        verbose_name = "حزب سياسي"
        verbose_name_plural = "الأحزاب السياسية"
        ordering = ['serial_number']


class PartyCandidate(models.Model):
    """مرشحو الأحزاب"""
    # نوع المجلس
    COUNCIL_TYPE_CHOICES = [
        ('parliament', 'مجلس النواب (البرلمان)'),
        ('provincial', 'مجلس المحافظة'),
    ]
    
    # كود المرشح الفريد (يبدأ بـ 03)
    candidate_code = models.CharField(max_length=10, unique=True, editable=False, null=True, blank=True,
                                      verbose_name="كود المرشح")
    
    # معلومات الحزب (اختيارية - للمرشحين المنتمين لأحزاب)
    party = models.ForeignKey(PoliticalParty, on_delete=models.CASCADE, 
                             related_name='candidates', verbose_name="الحزب",
                             null=True, blank=True)
    council_type = models.CharField(max_length=20, choices=COUNCIL_TYPE_CHOICES, 
                                    default='parliament', verbose_name="نوع المجلس")
    serial_number = models.IntegerField(verbose_name="الرقم التسلسلي في القائمة",
                                       null=True, blank=True)
    
    # Candidate Information
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    voter_number = models.CharField(max_length=50, blank=True, verbose_name="رقم الناخب")
    voter = models.ForeignKey('Voter', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='party_candidacies', verbose_name="من سجل الناخبين")
    
    # Contact & Details
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name="رقم الهاتف")
    photo = models.ImageField(upload_to='candidate_photos/', null=True, blank=True, 
                             verbose_name="الصورة الشخصية")
    biography = models.TextField(blank=True, verbose_name="السيرة الذاتية")
    
    # حقول إضافية من نموذج Candidate
    mother_name_triple = models.CharField(max_length=100, blank=True, verbose_name="اسم الأم ثلاثي")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="تاريخ الميلاد")
    address = models.CharField(max_length=200, blank=True, verbose_name="عنوان السكن")
    
    # معلومات مراكز الاقتراع والتسجيل
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    voting_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز الاقتراع")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    family_number = models.CharField(max_length=50, blank=True, verbose_name="رقم العائلة")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")
    status = models.CharField(max_length=50, blank=True, verbose_name="الحالة")
    
    # Vote Statistics (from Excel)
    stations_not_voted = models.IntegerField(default=0, verbose_name="محطات لم تصوت")
    stations_voted = models.IntegerField(default=0, verbose_name="محطات صوتت")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """
        1. توليد كود المرشح تلقائياً (03XX) عالمياً.
        2. تعيين الرقم التسلسلي (1-N) تلقائياً ضمن القائمة الحزبية.
        """
        # 1. Generate Global Candidate Code
        if not self.candidate_code:
            # البحث عن آخر كود مستخدم عالمياً واستخلاص الرقم
            # نستخدم regex أو startswith للتأكد، لكن هنا نفترض 03XXX
            last = PartyCandidate.objects.filter(candidate_code__startswith='03').order_by('-candidate_code').first()
            if last and last.candidate_code and len(last.candidate_code) > 2:
                try:
                    new_num = int(last.candidate_code[2:]) + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
            self.candidate_code = f"03{new_num:02d}"

        # 2. Auto-set Serial Number within Party (1-50)
        if self.party and not self.serial_number:
            # نحصل على أعلى رقم تسلسلي في هذا الحزب
            last_serial = PartyCandidate.objects.filter(party=self.party).aggregate(
                max_serial=models.Max('serial_number')
            )['max_serial'] or 0
            self.serial_number = last_serial + 1
            
        super().save(*args, **kwargs)
    
    def get_total_votes(self):
        """حساب إجمالي أصوات المرشح"""
        return VoteCount.objects.filter(candidate=self).aggregate(
            total=models.Sum('vote_count')
        )['total'] or 0
    
    def get_general_votes(self):
        """حساب أصوات التصويت العام"""
        return VoteCount.objects.filter(candidate=self, vote_type='general').aggregate(
            total=models.Sum('vote_count')
        )['total'] or 0
    
    def get_special_votes(self):
        """حساب أصوات التصويت الخاص"""
        return VoteCount.objects.filter(candidate=self, vote_type='special').aggregate(
            total=models.Sum('vote_count')
        )['total'] or 0
    
    def get_stations_voted_count(self):
        """عدد المحطات التي صوّت فيها"""
        return self.stations_voted
    
    def get_stations_not_voted_count(self):
        """عدد المحطات التي لم يُصوَّت فيها"""
        return self.stations_not_voted
    
    # أساليب لإدارة التسلسل الهرمي الانتخابي (المرتكزات، المعرفين، الناخبين، المراقبين)
    def get_anchors_count(self):
        """عدد المرتكزات للمرشح"""
        return self.anchors.count() if hasattr(self, 'anchors') else 0
    
    def get_introducers_count(self):
        """عدد المعرفين للمرشح عبر جميع المرتكزات"""
        try:
            from django.db.models import Count
            return Introducer.objects.filter(anchor__candidate=self).count()
        except:
            return 0
    
    def get_voters_count(self):
        """عدد الناخبين للمرشح عبر جميع المعرفين"""
        try:
            return Voter.objects.filter(introducer__anchor__candidate=self).count()
        except:
            return 0
    
    def get_monitors_count(self):
        """عدد المراقبين للمرشح"""
        return self.monitors.count() if hasattr(self, 'monitors') else 0
    
    def __str__(self):
        if self.party and self.serial_number:
            return f"{self.party.serial_number}-{self.serial_number} - {self.full_name}"
        return f"{self.candidate_code} - {self.full_name}"
    
    class Meta:
        verbose_name = "مرشح"
        verbose_name_plural = "المرشحون"
        ordering = ['-created_at']


class RegistrationCenter(models.Model):
    """مراكز التسجيل"""
    name = models.CharField(max_length=200, verbose_name="اسم مركز التسجيل")
    center_number = models.CharField(max_length=20, unique=True, verbose_name="رقم مركز التسجيل")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.center_number} - {self.name}"
    
    class Meta:
        verbose_name = "مركز تسجيل"
        verbose_name_plural = "مراكز التسجيل"
        ordering = ['center_number']


class PollingCenter(models.Model):
    """مراكز الاقتراع"""
    VOTING_TYPE_CHOICES = [
        ('general', 'اقتراع عام'),
        ('special', 'اقتراع خاص'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, verbose_name="اسم المركز")
    center_number = models.CharField(max_length=20, unique=True, verbose_name="رقم المركز")
    voting_type = models.CharField(max_length=20, choices=VOTING_TYPE_CHOICES, 
                                   default='general', verbose_name="نوع الاقتراع")
    
    # Relationship to Registration Center
    registration_center = models.ForeignKey(RegistrationCenter, on_delete=models.SET_NULL, 
                                           null=True, blank=True, related_name='polling_centers',
                                           verbose_name="مركز التسجيل")
    
    # Location & Area
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True,
                            verbose_name="المنطقة/الناحية")
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="الحي")
    location = models.CharField(max_length=200, blank=True, verbose_name="الموقع")
    address = models.TextField(blank=True, verbose_name="العنوان التفصيلي")
    
    # Registration Center Info
    registration_center_number = models.CharField(max_length=20, blank=True, 
                                                  verbose_name="رقم مركز التسجيل")
    registration_center_name = models.CharField(max_length=200, blank=True, 
                                               verbose_name="اسم مركز التسجيل")
    
    # Names (for General Voting)
    card_name = models.CharField(max_length=200, blank=True, 
                                 verbose_name="اسم المركز في البطاقة")
    actual_name = models.CharField(max_length=200, blank=True, 
                                  verbose_name="الاسم الفعلي للمركز")
    
    # Station Info
    station_count = models.IntegerField(default=1, verbose_name="عدد المحطات في المركز")
    total_registered_voters = models.IntegerField(default=0, verbose_name="إجمالي الناخبين المسجلين")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_stations_count(self):
        """عدد المحطات الفعلية"""
        return self.stations.count()
    
    def get_total_votes(self):
        """إجمالي الأصوات في المركز"""
        return VoteCount.objects.filter(station__center=self).aggregate(
            total=models.Sum('vote_count')
        )['total'] or 0
    
    def __str__(self):
        return f"{self.center_number} - {self.name}"
    
    class Meta:
        verbose_name = "مركز اقتراع"
        verbose_name_plural = "مراكز الاقتراع"
        ordering = ['center_number']


class PollingStation(models.Model):
    """محطات الاقتراع"""
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'جاري الجرد'),
        ('completed', 'مكتمل'),
        ('issues', 'يوجد مشاكل'),
    ]
    
    center = models.ForeignKey(PollingCenter, on_delete=models.CASCADE,
                              related_name='stations', verbose_name="المركز")
    station_number = models.IntegerField(verbose_name="رقم المحطة في المركز")
    full_number = models.CharField(max_length=50, unique=True, editable=False,
                                   verbose_name="الرقم الكامل للمحطة")
    
    # Vote Statistics
    registered_voters = models.IntegerField(default=0, verbose_name="عدد الناخبين المسجلين")
    total_ballots_received = models.IntegerField(default=0, verbose_name="إجمالي الأوراق المستلمة")
    valid_votes = models.IntegerField(default=0, verbose_name="الأصوات الصحيحة")
    invalid_votes = models.IntegerField(default=0, verbose_name="الأصوات الباطلة")
    
    # Status
    counting_status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                      default='pending', verbose_name="حالة الجرد")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Generate full number
        if not self.full_number:
            self.full_number = f"{self.center.center_number}-{self.station_number}"
        super().save(*args, **kwargs)
    
    def get_total_votes(self):
        """إجمالي الأصوات المسجلة"""
        return VoteCount.objects.filter(station=self).aggregate(
            total=models.Sum('vote_count')
        )['total'] or 0
    
    def __str__(self):
        return f"{self.full_number} - {self.center.name}"
    
    class Meta:
        verbose_name = "محطة اقتراع"
        verbose_name_plural = "محطات الاقتراع"
        ordering = ['center__center_number', 'station_number']
        unique_together = ['center', 'station_number']


class VoteCount(models.Model):
    """جرد الأصوات"""
    VOTE_TYPE_CHOICES = [
        ('general', 'تصويت عام'),
        ('special', 'تصويت خاص'),
    ]
    
    station = models.ForeignKey(PollingStation, on_delete=models.CASCADE,
                               related_name='vote_counts', verbose_name="المحطة")
    candidate = models.ForeignKey(PartyCandidate, on_delete=models.CASCADE,
                                 related_name='vote_counts', verbose_name="المرشح")
    vote_count = models.IntegerField(default=0, verbose_name="عدد الأصوات")
    vote_type = models.CharField(max_length=20, choices=VOTE_TYPE_CHOICES, 
                                 default='general', verbose_name="نوع التصويت")
    
    # Metadata
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='entered_vote_counts',
                                  verbose_name="أدخلت بواسطة")
    entered_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ ووقت الإدخال")
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    def __str__(self):
        return f"{self.station.full_number} - {self.candidate.full_name}: {self.vote_count} ({self.get_vote_type_display()})"
    
    class Meta:
        verbose_name = "جرد أصوات"
        verbose_name_plural = "جرد الأصوات"
        ordering = ['-entered_at']
        unique_together = ['station', 'candidate', 'vote_type']


# ==================== Electoral Public Registration (المرتكزات) ====================
# Based on Video 1: 16-52-51.mp4

class ElectoralPublic(models.Model):
    """المرتكزات - الأشخاص المرتبطون بالمرشحين"""
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
    ]
    
    # معلومات المرتكز
    candidate = models.ForeignKey('PartyCandidate', on_delete=models.CASCADE,
                                  null=True, blank=True,
                                  related_name='anchors_support', verbose_name="المرشح")
    voter_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    phone_number = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                                    help_text="مثال: 07XXXXXXXXX",
                                    validators=[validate_phone_number])
    password = models.CharField(max_length=128, verbose_name="كلمة المرور",
                               help_text="كلمة مرور للدخول إلى النظام")
    
    # Auto-filled from Voter DB
    full_name = models.CharField(max_length=150, blank=True, verbose_name="الاسم الكامل")
    voting_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز الاقتراع")
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="الحالة")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التسجيل")
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_candidate_code(self):
        """الحصول على كود المرشح"""
        if self.candidate and hasattr(self.candidate, 'candidate_code'):
            return self.candidate.candidate_code
        return "-"
    
    def __str__(self):
        return f"{self.full_name or self.voter_number} - {self.candidate.full_name if self.candidate else 'بدون مرشح'}"
    
    class Meta:
        verbose_name = "مرتكز"
        verbose_name_plural = "المرتكزات"
        ordering = ['-registered_at']
        unique_together = []


# ==================== Personal Voter Record (المعرفين) ====================
# Based on Video 2: 17-02-52.mp4

class PersonalVoterRecord(models.Model):
    """المعرفين - أشخاص يرتبطون بالمرتكزات ويجلبون الناخبين"""
    
    # معلومات المعرف
    anchor = models.ForeignKey('ElectoralPublic', on_delete=models.CASCADE,
                              null=True, blank=True,
                              related_name='introducers', verbose_name="المرتكز")
    anchor_code = models.CharField(max_length=50, blank=True, verbose_name="كود المرتكز",
                                   help_text="كود المرتكز للربط به")
    
    # معلومات المعرف (من قاعدة بيانات الناخبين)
    voter_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    phone_number = models.CharField(max_length=11, verbose_name="رقم الهاتف",
                                    validators=[validate_phone_number])
    
    # معلومات إضافية (تلقائية)
    voting_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز الاقتراع")
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")
    family_number = models.CharField(max_length=50, blank=True, verbose_name="رقم العائلة")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    
    # التصنيف
    CLASSIFICATION_CHOICES = [
        ('supporter', 'مؤيد'),
        ('neutral', 'محايد'),
        ('opponent', 'معارض'),
        ('unknown', 'غير محدد'),
    ]
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, 
                                      default='supporter', verbose_name="التصنيف")
    
    # ملاحظات
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    # الطوابع الزمنية
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_candidate(self):
        """الحصول على المرشح عبر المرتكز"""
        if self.anchor and self.anchor.candidate:
            return self.anchor.candidate
        return None
    
    def get_voters_count(self):
        """عدد الناخبين المرتبطين بهذا المعرف"""
        return self.voters.count()
    
    def __str__(self):
        return f"{self.full_name} ({self.voter_number})"
    
    class Meta:
        verbose_name = "معرف"
        verbose_name_plural = "المعرفين"
        ordering = ['-added_at']


class IntroducerVoter(models.Model):
    """ناخبين المعرف - الناخبين الذين يجلبهم المعرف"""
    
    introducer = models.ForeignKey(PersonalVoterRecord, on_delete=models.CASCADE,
                                   related_name='voters', verbose_name="المعرف")
    
    # معلومات الناخب
    voter_number = models.CharField(max_length=50, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    
    # معلومات تلقائية
    voting_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز الاقتراع")
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")
    family_number = models.CharField(max_length=50, blank=True, verbose_name="رقم العائلة")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    
    # التصنيف
    CLASSIFICATION_CHOICES = [
        ('supporter', 'مؤيد'),
        ('neutral', 'محايد'),
        ('opponent', 'معارض'),
        ('unknown', 'غير محدد'),
    ]
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES,
                                      default='supporter', verbose_name="التصنيف")
    
    # ملاحظات
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    # الطوابع الزمنية
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} ({self.voter_number}) - {self.introducer.full_name}"
    
    class Meta:
        verbose_name = "ناخب معرف"
        verbose_name_plural = "ناخبين المعرفين"
        ordering = ['-added_at']
        unique_together = ['introducer', 'voter_number']


# ==================== Observer Registration (تسجيل المراقبين) ====================
# Based on Video 3: 17-05-27.mp4

class ObserverRegistration(models.Model):
    """تسجيل المراقبين والوكلاء - نظام موحد"""
    
    OBSERVER_TYPE_CHOICES = [
        ('candidate_monitor', 'مراقب مرشح'),
        ('entity_agent', 'وكيل كيان سياسي'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'ذكر'),
        ('female', 'أنثى'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'أعزب/عزباء'),
        ('married', 'متزوج/ة'),
        ('divorced', 'مطلق/ة'),
        ('widowed', 'أرمل/ة'),
    ]
    
    EDUCATION_CHOICES = [
        ('primary', 'ابتدائي'),
        ('intermediate', 'متوسط'),
        ('secondary', 'إعدادي'),
        ('diploma', 'دبلوم'),
        ('bachelors', 'بكالوريوس'),
        ('masters', 'ماجستير'),
        ('doctorate', 'دكتوراه'),
        ('other', 'أخرى'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('approved', 'معتمد'),
        ('badge_issued', 'تم إصدار الباج'),
        ('rejected', 'مرفوض'),
    ]
    
    # نوع المسجل: مراقب مرشح أم وكيل كيان
    observer_type = models.CharField(max_length=20, choices=OBSERVER_TYPE_CHOICES,
                                     default='candidate_monitor', verbose_name="النوع")
    
    # كود المرشح (فقط للمراقبين)
    candidate_code = models.CharField(max_length=50, blank=True, verbose_name="كود المرشح",
                                     help_text="يتم ملؤه فقط للمراقبين")
    linked_candidate = models.ForeignKey('PartyCandidate', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='observer_registrations', verbose_name="المرشح المرتبط")
    
    # معلومات أساسية
    voter_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الناخب",
                                     validators=[validate_voter_number_required])
    phone_number = models.CharField(max_length=11, unique=True, verbose_name="رقم الهاتف",
                                    validators=[validate_phone_number])
    
    # معلومات تلقائية من قاعدة بيانات الناخبين
    full_name = models.CharField(max_length=150, verbose_name="الاسم الكامل")
    mother_name = models.CharField(max_length=100, blank=True, verbose_name="اسم الأم")
    national_id = models.CharField(max_length=50, blank=True, verbose_name="رقم البطاقة الوطنية الموحدة")
    voting_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز الاقتراع")
    voting_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز الاقتراع")
    registration_center_name = models.CharField(max_length=150, blank=True, verbose_name="اسم مركز التسجيل")
    registration_center_number = models.CharField(max_length=50, blank=True, verbose_name="رقم مركز التسجيل")
    station_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المحطة")
    governorate = models.CharField(max_length=50, default="البصرة", verbose_name="المحافظة")
    
    # معلومات شخصية
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="تاريخ الميلاد")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male', verbose_name="الجنس")
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, 
                                      default='single', verbose_name="الحالة الاجتماعية")
    education = models.CharField(max_length=20, choices=EDUCATION_CHOICES, 
                                 default='secondary', verbose_name="التحصيل الدراسي")
    
    # صور وتحقق
    photo = models.ImageField(upload_to='observer_photos/', null=True, blank=True, 
                             verbose_name="الصورة الشخصية")
    face_capture = models.ImageField(upload_to='observer_face_captures/', null=True, blank=True,
                                     verbose_name="صورة التحقق الحيوي")
    face_captured = models.BooleanField(default=False, verbose_name="تم التقاط الوجه")
    face_capture_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ التقاط الوجه")
    
    # معلومات الباج
    badge_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="رقم الباج")
    badge_issued = models.BooleanField(default=False, verbose_name="تم إصدار الباج")
    badge_issue_date = models.DateField(null=True, blank=True, verbose_name="تاريخ إصدار الباج")
    
    # المستندات
    photo_submitted = models.BooleanField(default=False, verbose_name="تم تقديم الصورة الشخصية")
    voter_card_submitted = models.BooleanField(default=False, verbose_name="تم تقديم بطاقة الناخب")
    national_id_submitted = models.BooleanField(default=False, verbose_name="تم تقديم البطاقة الوطنية")
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")
    password = models.CharField(max_length=128, blank=True, verbose_name="كلمة المرور")
    
    # الطوابع الزمنية
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التسجيل")
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الموافقة")
    
    def __str__(self):
        type_label = "مراقب" if self.observer_type == 'candidate_monitor' else "وكيل"
        return f"{type_label}: {self.full_name} ({self.voter_number})"
    
    def get_age(self):
        """حساب العمر"""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    class Meta:
        verbose_name = "تسجيل مراقب/وكيل"
        verbose_name_plural = "تسجيلات المراقبين والوكلاء"
        ordering = ['-registered_at']


# ==================== Barcode Scanning System (IHEC Style) ====================

class BarcodeScanSession(models.Model):
    """جلسة مسح الباركود لجرد الأصوات"""
    
    VOTE_TYPE_CHOICES = [
        ('general', 'تصويت عام'),
        ('special', 'تصويت خاص'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشطة'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    ]
    
    # Session Info
    session_code = models.CharField(max_length=50, unique=True, editable=False,
                                    verbose_name="رمز الجلسة")
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="المُشغِّل")
    
    # Voting Type
    vote_type = models.CharField(max_length=20, choices=VOTE_TYPE_CHOICES,
                                 default='general', verbose_name="نوع التصويت")
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="بدء الجلسة")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="انتهاء الجلسة")
    
    # Statistics
    total_scans = models.IntegerField(default=0, verbose_name="عدد المسحات")
    successful_scans = models.IntegerField(default=0, verbose_name="مسحات ناجحة")
    failed_scans = models.IntegerField(default=0, verbose_name="مسحات فاشلة")
    duplicate_scans = models.IntegerField(default=0, verbose_name="مسحات مكررة")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                             default='active', verbose_name="حالة الجلسة")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    def save(self, *args, **kwargs):
        """توليد رمز الجلسة تلقائياً"""
        if not self.session_code:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.session_code = f"SCAN-{timestamp}"
        super().save(*args, **kwargs)
    
    def get_success_rate(self):
        """نسبة النجاح"""
        if self.total_scans == 0:
            return 0
        return round((self.successful_scans / self.total_scans) * 100, 2)
    
    def __str__(self):
        return f"{self.session_code} - {self.get_vote_type_display()}"
    
    class Meta:
        verbose_name = "جلسة مسح باركود"
        verbose_name_plural = "جلسات مسح الباركود"
        ordering = ['-started_at']


class BarcodeScanRecord(models.Model):
    """سجل مسح الباركود"""
    
    STATUS_CHOICES = [
        ('pending', 'قيد المعالجة'),
        ('validated', 'تم التحقق'),
        ('processed', 'تم المعالجة'),
        ('rejected', 'مرفوض'),
        ('duplicate', 'مكرر'),
        ('error', 'خطأ'),
    ]
    
    # Session Link
    session = models.ForeignKey(BarcodeScanSession, on_delete=models.CASCADE,
                               related_name='scans', verbose_name="الجلسة")
    
    # Raw Barcode Data
    barcode_data = models.TextField(verbose_name="بيانات الباركود الخام")
    barcode_type = models.CharField(max_length=50, blank=True, 
                                   verbose_name="نوع الباركود",
                                   help_text="مثل: CODE_128, QR_CODE, EAN_13")
    
    # Extracted Information
    center_number = models.CharField(max_length=50, blank=True,
                                    verbose_name="رقم المركز المستخرج")
    station_number = models.CharField(max_length=50, blank=True,
                                     verbose_name="رقم المحطة المستخرجة")
    vote_type = models.CharField(max_length=20, blank=True,
                                verbose_name="نوع التصويت المستخرج")
    
    # Links to Database
    polling_center = models.ForeignKey(PollingCenter, on_delete=models.SET_NULL,
                                      null=True, blank=True,
                                      related_name='barcode_scans',
                                      verbose_name="المركز المرتبط")
    polling_station = models.ForeignKey(PollingStation, on_delete=models.SET_NULL,
                                       null=True, blank=True,
                                       related_name='barcode_scans',
                                       verbose_name="المحطة المرتبطة")
    
    # Vote Counts Data (JSON format for flexibility)
    # Structure: {"candidate_id": vote_count, ...}
    vote_data = models.JSONField(null=True, blank=True,
                                verbose_name="بيانات الأصوات",
                                help_text="بيانات الأصوات بصيغة JSON")
    
    # Additional extracted metadata
    scan_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الاقتراع")
    total_votes = models.IntegerField(null=True, blank=True, verbose_name="إجمالي الأصوات")
    valid_votes = models.IntegerField(null=True, blank=True, verbose_name="أصوات صحيحة")
    invalid_votes = models.IntegerField(null=True, blank=True, verbose_name="أصوات باطلة")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                             default='pending', verbose_name="الحالة")
    validation_errors = models.TextField(blank=True, verbose_name="أخطاء التحقق")
    validation_warnings = models.TextField(blank=True, verbose_name="تحذيرات التحقق")
    
    # Processing
    is_processed = models.BooleanField(default=False, verbose_name="تمت المعالجة")
    processed_at = models.DateTimeField(null=True, blank=True,
                                       verbose_name="وقت المعالجة")
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                    null=True, blank=True,
                                    related_name='processed_scans',
                                    verbose_name="تمت المعالجة بواسطة")
    
    # System
    scanned_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت المسح")
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='barcode_scans',
                                verbose_name="المُشغِّل")
    
    # Image of scanned barcode (optional)
    barcode_image = models.ImageField(upload_to='barcode_scans/', null=True, blank=True,
                                     verbose_name="صورة الباركود")
    
    def __str__(self):
        if self.center_number and self.station_number:
            return f"مسح: {self.center_number}-{self.station_number} ({self.get_status_display()})"
        return f"مسح: {self.barcode_data[:30]}... ({self.get_status_display()})"
    
    def get_full_station_code(self):
        """الحصول على الرمز الكامل للمحطة"""
        if self.center_number and self.station_number:
            return f"{self.center_number}-{self.station_number}"
        return None
    
    class Meta:
        verbose_name = "سجل مسح باركود"
        verbose_name_plural = "سجلات مسح الباركود"
        ordering = ['-scanned_at']
        indexes = [
            models.Index(fields=['center_number', 'station_number']),
            models.Index(fields=['status']),
            models.Index(fields=['session', 'scanned_at']),
        ]


# ==================== Attendance and Login Tracking ====================

class AttendanceRecord(models.Model):
    """سجل حضور وانصراف الوكلاء والمراقبين"""
    
    RECORD_TYPE_CHOICES = [
        ('agent', 'وكيل كيان سياسي'),
        ('monitor', 'مراقب مرشح'),
    ]
    
    STATUS_CHOICES = [
        ('checked_in', 'حضر'),
        ('checked_out', 'انصرف'),
    ]
    
    # Agent or Monitor info
    agent = models.ForeignKey('PoliticalEntityAgent', on_delete=models.CASCADE, 
                             related_name='attendance_records', null=True, blank=True,
                             verbose_name="الوكيل")
    monitor = models.ForeignKey('CandidateMonitor', on_delete=models.CASCADE,
                               related_name='attendance_records', null=True, blank=True,
                               verbose_name="المراقب")
    
    # Center Director who recorded
    recorded_by = models.ForeignKey('CenterDirector', on_delete=models.CASCADE,
                                   related_name='attendance_records',
                                   verbose_name="سجل بواسطة")
    
    # Record details
    record_type = models.CharField(max_length=10, choices=RECORD_TYPE_CHOICES,
                                   verbose_name="نوع السجل")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES,
                             verbose_name="الحالة")
    
    # Timestamps
    check_in_time = models.DateTimeField(null=True, blank=True,
                                        verbose_name="وقت الحضور")
    check_out_time = models.DateTimeField(null=True, blank=True,
                                         verbose_name="وقت الانصراف")
    
    # Additional info
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_person_name(self):
        """الحصول على اسم الشخص"""
        if self.agent:
            return self.agent.full_name
        elif self.monitor:
            return self.monitor.full_name
        return "غير محدد"
    
    def get_duration(self):
        """حساب مدة التواجد"""
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            hours = duration.total_seconds() / 3600
            return f"{hours:.2f} ساعة"
        return "لم ينصرف بعد"
    
    def __str__(self):
        return f"{self.get_person_name()} - {self.get_status_display()} - {self.recorded_by.assigned_center_number}"
    
    class Meta:
        verbose_name = "سجل حضور"
        verbose_name_plural = "سجلات الحضور والانصراف"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['record_type', 'status']),
            models.Index(fields=['-created_at']),
        ]


class DirectorLoginLog(models.Model):
    """سجل تسجيل دخول مدراء المراكز"""
    
    director = models.ForeignKey('CenterDirector', on_delete=models.CASCADE,
                                related_name='login_logs',
                                verbose_name="مدير المركز")
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                            verbose_name="المستخدم")
    
    login_time = models.DateTimeField(auto_now_add=True,
                                     verbose_name="وقت تسجيل الدخول")
    logout_time = models.DateTimeField(null=True, blank=True,
                                      verbose_name="وقت تسجيل الخروج")
    
    ip_address = models.GenericIPAddressField(null=True, blank=True,
                                             verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, verbose_name="متصفح المستخدم")
    
    def get_session_duration(self):
        """حساب مدة الجلسة"""
        if self.logout_time:
            duration = self.logout_time - self.login_time
            hours = duration.total_seconds() / 3600
            return f"{hours:.2f} ساعة"
        return "جلسة نشطة"
    
    def __str__(self):
        return f"{self.director.full_name} - {self.login_time.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = "سجل تسجيل دخول مدير"
        verbose_name_plural = "سجلات تسجيل دخول المدراء"
        ordering = ['-login_time']


# ==================== Unified Communication System ====================

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class CommunicationLog(models.Model):
    """سجل الاتصالات الموحد لجميع الفئات"""
    
    CALL_STATUS_CHOICES = [
        ('answered', 'تم الرد'),
        ('busy', 'مشغول'),
        ('no_answer', 'لا يوجد رد'),
        ('wrong_number', 'رقم خاطئ'),
        ('switched_off', 'مغلق'),
        ('later', 'طلب الاتصال لاحقاً'),
    ]
    
    # من قام بالاتصال
    caller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="المتصل")
    
    # الشخص الذي تم الاتصال به (Generic Relation)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # تفاصيل الاتصال
    phone_number = models.CharField(max_length=20, verbose_name="رقم الهاتف", null=True)
    call_status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES, verbose_name="حالة الاتصال", null=True)
    outcome = models.TextField(blank=True, verbose_name="نتيجة الاتصال")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت الاتصال")
    
    def __str__(self):
        return f"اتصال بـ {self.phone_number} - {self.get_call_status_display()}"
    
    class Meta:
        verbose_name = "سجل اتصال"
        verbose_name_plural = "سجلات الاتصالات"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
        ]

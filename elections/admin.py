from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    UserProfile, UserRole,
    Area, Neighborhood, Voter, Candidate, Anchor, Introducer,
    CandidateMonitor, CommunicationLog, CampaignTask,
    Organization, CivilSocietyObserver, InternationalObserver, PoliticalEntityAgent, CenterDirector,
    PoliticalParty, PartyCandidate, PollingCenter, PollingStation, VoteCount,
    BarcodeScanSession, BarcodeScanRecord, SubOperationRoom, RegistrationCenter
)



# ==================== User Profile Inline ====================

class UserProfileInline(admin.StackedInline):
    """عرض ملف المستخدم مع نموذج المستخدم"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'الملف الشخصي والصلاحيات'
    
    fieldsets = (
        ('الدور والصلاحيات', {
            'fields': ('role', 'can_export_reports', 'can_delete_records', 'can_view_sensitive_data')
        }),
        ('التخصيص الجغرافي', {
            'fields': ('assigned_area', 'assigned_neighborhood')
        }),
        ('معلومات إضافية', {
            'fields': ('phone', 'employee_id', 'notes')
        }),
        ('الحالة', {
            'fields': ('is_active', 'activation_date', 'deactivation_date')
        }),
    )


class CustomUserAdmin(BaseUserAdmin):
    """تخصيص صفحة إدارة المستخدمين لإضافة ملف التعريف"""
    inlines = (UserProfileInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# إلغاء تسجيل User الافتراضي وتسجيل النسخة المخصصة
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """إدارة ملفات تعريف المستخدمين"""
    list_display = ['user', 'role', 'assigned_area', 'can_export_reports', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'can_export_reports', 'can_delete_records', 'assigned_area']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone', 'employee_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('المستخدم', {
            'fields': ('user',)
        }),
        ('الدور والصلاحيات', {
            'fields': ('role', 'can_export_reports', 'can_delete_records', 'can_view_sensitive_data')
        }),
        ('التخصيص الجغرافي', {
            'fields': ('assigned_area', 'assigned_neighborhood'),
            'description': 'تحديد منطقة محددة لعمل المستخدم'
        }),
        ('معلومات إضافية', {
            'fields': ('phone', 'employee_id', 'notes')
        }),
        ('الحالة', {
            'fields': ('is_active', 'activation_date', 'deactivation_date')
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Admin can see all users
        return qs
    
    # Add custom actions
    actions = ['activate_users', 'deactivate_users', 'grant_export_permission', 'revoke_export_permission']
    
    @admin.action(description='تفعيل المستخدمين المحددين')
    def activate_users(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(is_active=True, activation_date=timezone.now().date())
        self.message_user(request, f'تم تفعيل {count} مستخدم بنجاح.')
    
    @admin.action(description='تعطيل المستخدمين المحددين')
    def deactivate_users(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(is_active=False, deactivation_date=timezone.now().date())
        self.message_user(request, f'تم تعطيل {count} مستخدم بنجاح.')
    
    @admin.action(description='منح صلاحية تصدير التقارير')
    def grant_export_permission(self, request, queryset):
        count = queryset.update(can_export_reports=True)
        self.message_user(request, f'تم منح صلاحية التصدير لـ {count} مستخدم.')
    
    @admin.action(description='إلغاء صلاحية تصدير التقارير')
    def revoke_export_permission(self, request, queryset):
        count = queryset.update(can_export_reports=False)
        self.message_user(request, f'تم إلغاء صلاحية التصدير من {count} مستخدم.')



@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Neighborhood)
class NeighborhoodAdmin(admin.ModelAdmin):
    list_display = ['name', 'area']
    list_filter = ['area']
    search_fields = ['name']


@admin.register(RegistrationCenter)
class RegistrationCenterAdmin(admin.ModelAdmin):
    list_display = ['center_number', 'name', 'governorate', 'get_polling_centers_count']
    search_fields = ['center_number', 'name']
    list_filter = ['governorate']
    
    def get_polling_centers_count(self, obj):
        return obj.polling_centers.count()
    get_polling_centers_count.short_description = 'عدد مراكز الاقتراع'


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ['voter_number', 'full_name', 'phone', 'classification', 'introducer', 'polling_center', 'polling_station']
    list_filter = ['classification', 'area', 'introducer', 'polling_center', 'registration_center_fk']
    search_fields = ['voter_number', 'full_name', 'phone']
    readonly_fields = ['voter_code', 'created_at', 'updated_at']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('voter_number', 'full_name', 'date_of_birth', 'mother_name', 'family_number')
        }),
        ('معلومات الاتصال', {
            'fields': ('phone',)
        }),
        ('الموقع', {
            'fields': ('governorate', 'area', 'neighborhood')
        }),
        ('الهيكل الانتخابي (روابط)', {
            'fields': ('polling_center', 'polling_station', 'registration_center_fk'),
            'description': 'الروابط المنطقية مع الهيكل الانتخابي'
        }),
        ('معلومات مراكز الاقتراع (نصية)', {
            'fields': ('voting_center_number', 'voting_center_name', 'registration_center_number', 
                       'registration_center_name', 'station_number', 'status'),
            'classes': ('collapse',)
        }),
        ('الحملة الانتخابية', {
            'fields': ('introducer', 'voter_code', 'classification', 'notes')
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['candidate_code', 'full_name', 'phone', 'voting_center_name']
    search_fields = ['candidate_code', 'full_name', 'voter_number', 'phone']
    readonly_fields = ['candidate_code', 'created_at', 'updated_at']
    
    fieldsets = (
        ('كود المرشح', {
            'fields': ('candidate_code',)
        }),
        ('معلومات أساسية', {
            'fields': ('voter_number', 'full_name', 'mother_name_triple', 'date_of_birth', 'family_number')
        }),
        ('معلومات الاتصال', {
            'fields': ('phone', 'address')
        }),
        ('مراكز الاقتراع', {
            'fields': ('governorate', 'voting_center_number', 'voting_center_name', 
                       'registration_center_number', 'registration_center_name', 
                       'station_number', 'status')
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Anchor)
class AnchorAdmin(admin.ModelAdmin):
    list_display = ['anchor_code', 'full_name', 'candidate', 'phone']
    list_filter = ['candidate']
    search_fields = ['anchor_code', 'full_name', 'voter_number', 'phone']
    readonly_fields = ['anchor_code', 'created_at', 'updated_at']


@admin.register(Introducer)
class IntroducerAdmin(admin.ModelAdmin):
    list_display = ['introducer_code', 'full_name', 'anchor', 'phone']
    list_filter = ['anchor__candidate']
    search_fields = ['introducer_code', 'full_name', 'voter_number', 'phone']
    readonly_fields = ['introducer_code', 'created_at', 'updated_at']


@admin.register(CandidateMonitor)
class CandidateMonitorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'candidate', 'phone', 'status', 'created_at']
    list_filter = ['candidate', 'status']
    search_fields = ['full_name', 'voter_number', 'phone']


@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'caller', 'call_status', 'created_at']
    list_filter = ['call_status', 'created_at']
    search_fields = ['phone_number', 'outcome']
    date_hierarchy = 'created_at'


@admin.register(CampaignTask)
class CampaignTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'priority', 'status', 'due_date', 'created_at']
    list_filter = ['priority', 'status', 'target_area']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'


# ==================== Observer and Agent Admin ====================

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'registration_number', 'is_active', 'deposit_paid']
    list_filter = ['type', 'is_active', 'deposit_paid']
    search_fields = ['name', 'registration_number']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'type', 'registration_number')
        }),
        ('معلومات الاتصال', {
            'fields': ('email', 'phone', 'address')
        }),
        ('الإيداع المالي (للكيانات السياسية)', {
            'fields': ('deposit_amount', 'deposit_paid'),
            'classes': ('collapse',)
        }),
        ('التسجيل', {
            'fields': ('registration_date', 'is_active', 'notes')
        }),
    )


@admin.register(CivilSocietyObserver)
class CivilSocietyObserverAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'organization', 'voter_number', 'monitoring_center_number', 
                   'status', 'badge_issued', 'registration_date']
    list_filter = ['organization', 'status', 'badge_issued', 'governorate']
    search_fields = ['full_name', 'voter_number', 'phone', 'monitoring_center_number']
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('المنظمة', {
            'fields': ('organization',)
        }),
        ('معلومات شخصية', {
            'fields': ('full_name', 'age', 'voter_number', 'national_id')
        }),
        ('معلومات الاتصال', {
            'fields': ('phone', 'email', 'address')
        }),
        ('مركز المراقبة المخصص', {
            'fields': ('monitoring_center_number', 'monitoring_center_name', 'governorate')
        }),
        ('المستندات المطلوبة', {
            'fields': ('photo_submitted', 'voter_card_submitted', 'national_id_submitted', 'has_biometric_card')
        }),
        ('معلومات الباج', {
            'fields': ('badge_number', 'badge_issued', 'badge_issue_date')
        }),
        ('الحالة', {
            'fields': ('status', 'approval_date', 'added_by', 'notes')
        }),
    )


@admin.register(InternationalObserver)
class InternationalObserverAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'organization', 'nationality', 'passport_number', 
                   'status', 'badge_issued', 'registration_date']
    list_filter = ['organization', 'status', 'badge_issued', 'nationality']
    search_fields = ['full_name', 'passport_number', 'phone', 'email']
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('المنظمة/السفارة', {
            'fields': ('organization',)
        }),
        ('معلومات شخصية', {
            'fields': ('full_name', 'nationality', 'passport_number')
        }),
        ('معلومات الاتصال', {
            'fields': ('phone', 'email')
        }),
        ('مناطق المراقبة المخصصة', {
            'fields': ('monitoring_governorate', 'monitoring_centers')
        }),
        ('معلومات الباج', {
            'fields': ('badge_number', 'badge_issued', 'badge_issue_date')
        }),
        ('الحالة', {
            'fields': ('status', 'approval_date', 'added_by', 'notes')
        }),
    )


# ==================== Sub-Operation Rooms Admin ====================

@admin.register(SubOperationRoom)
class SubOperationRoomAdmin(admin.ModelAdmin):
    """إدارة غرف العمليات الفرعية"""
    list_display = ['room_code', 'name', 'supervisor', 'is_active', 
                   'get_introducers_count', 'get_voters_count', 
                   'get_directors_count', 'get_agents_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['room_code', 'name', 'location', 'supervisor__username']
    readonly_fields = ['room_code', 'created_at', 'updated_at',
                      'get_introducers_count', 'get_voters_count',
                      'get_directors_count', 'get_agents_count',
                      'get_total_people_count']
    
    fieldsets = (
        ('كود الغرفة', {
            'fields': ('room_code',)
        }),
        ('معلومات أساسية', {
            'fields': ('name', 'description', 'supervisor')
        }),
        ('معلومات الاتصال', {
            'fields': ('phone', 'location')
        }),
        ('الحالة', {
            'fields': ('is_active',)
        }),
        ('الإحصائيات', {
            'fields': ('get_introducers_count', 'get_voters_count', 
                      'get_directors_count', 'get_agents_count',
                      'get_total_people_count'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom actions
    actions = ['activate_rooms', 'deactivate_rooms']
    
    @admin.action(description='تفعيل الغرف المحددة')
    def activate_rooms(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'تم تفعيل {count} غرفة بنجاح.')
    
    @admin.action(description='تعطيل الغرف المحددة')
    def deactivate_rooms(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'تم تعطيل {count} غرفة بنجاح.')


@admin.register(PoliticalEntityAgent)
class PoliticalEntityAgentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'political_entity', 'voter_number', 'assigned_center_number', 
                   'status', 'badge_issued', 'interview_completed', 'registration_date']
    list_filter = ['political_entity', 'status', 'badge_issued', 'interview_completed', 'governorate']
    search_fields = ['full_name', 'voter_number', 'phone', 'assigned_center_number']
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('الكيان السياسي', {
            'fields': ('political_entity',)
        }),
        ('معلومات شخصية', {
            'fields': ('full_name', 'age', 'voter_number', 'national_id')
        }),
        ('معلومات الاتصال', {
            'fields': ('phone', 'email', 'address', 'governorate')
        }),
        ('المحطة المخصصة', {
            'fields': ('assigned_center_number', 'assigned_center_name', 'assigned_station_number'),
            'description': 'مراقب واحد لكل محطة اقتراع حسب تعليمات المفوضية'
        }),
        ('المستندات المطلوبة', {
            'fields': ('photo_submitted', 'voter_card_submitted', 'national_id_submitted', 'has_biometric_card')
        }),
        ('معلومات الباج', {
            'fields': ('badge_number', 'badge_issued', 'badge_issue_date')
        }),
        ('المقابلة', {
            'fields': ('interview_scheduled', 'interview_date', 'interview_completed')
        }),
        ('الحالة', {
            'fields': ('status', 'verification_date', 'approval_date', 'added_by', 'notes')
        }),
    )


# ==================== Vote Counting Admin ====================

@admin.register(PoliticalParty)
class PoliticalPartyAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'name', 'get_candidates_count', 'get_total_votes']
    search_fields = ['name', 'serial_number']
    ordering = ['serial_number']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'serial_number', 'description')
        }),
        ('التصميم', {
            'fields': ('logo', 'color')
        }),
    )


@admin.register(PartyCandidate)
class PartyCandidateAdmin(admin.ModelAdmin):
    list_display = ['party', 'serial_number', 'full_name', 'voter_number', 'get_total_votes']
    list_filter = ['party']
    search_fields = ['full_name', 'voter_number']
    ordering = ['party__serial_number', 'serial_number']
    
    fieldsets = (
        ('الحزب والرقم', {
            'fields': ('party', 'serial_number')
        }),
        ('معلومات المرشح', {
            'fields': ('full_name', 'voter_number', 'voter', 'phone')
        }),
        ('إضافي', {
            'fields': ('photo', 'biography'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PollingCenter)
class PollingCenterAdmin(admin.ModelAdmin):
    list_display = ['center_number', 'name', 'voting_type', 'registration_center', 'station_count', 'get_stations_count']
    list_filter = ['voting_type', 'governorate', 'area', 'registration_center']
    search_fields = ['center_number', 'name', 'location', 
                    'registration_center_number', 'registration_center_name', 
                    'card_name', 'actual_name']
    ordering = ['center_number']
    list_per_page = 50
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('center_number', 'name', 'voting_type')
        }),
        ('الموقع', {
            'fields': ('governorate', 'area', 'neighborhood', 'location', 'address')
        }),
        ('مركز التسجيل', {
            'fields': ('registration_center', 'registration_center_number', 'registration_center_name')
        }),
        ('أسماء المركز', {
            'fields': ('card_name', 'actual_name'),
            'description': 'للاقتراع العام فقط'
        }),
        ('معلومات المحطات', {
            'fields': ('station_count', 'total_registered_voters')
        }),
    )


@admin.register(PollingStation)
class PollingStationAdmin(admin.ModelAdmin):
    list_display = ['full_number', 'center', 'station_number', 'counting_status', 'valid_votes', 'invalid_votes']
    list_filter = ['counting_status', 'center__area']
    search_fields = ['full_number', 'center__name', 'center__center_number']
    readonly_fields = ['full_number']
    ordering = ['center__center_number', 'station_number']
    
    fieldsets = (
        ('المحطة', {
            'fields': ('center', 'station_number', 'full_number')
        }),
        ('الإحصائيات', {
            'fields': ('registered_voters', 'total_ballots_received', 'valid_votes', 'invalid_votes')
        }),
        ('الحالة', {
            'fields': ('counting_status', 'notes')
        }),
    )


@admin.register(VoteCount)
class VoteCountAdmin(admin.ModelAdmin):
    list_display = ['station', 'candidate', 'vote_count', 'entered_by', 'entered_at']
    list_filter = ['candidate__party', 'station__center__area', 'entered_at']
    search_fields = ['station__full_number', 'candidate__full_name']
    date_hierarchy = 'entered_at'
    readonly_fields = ['entered_at', 'updated_at']
    
    fieldsets = (
        ('جرد الأصوات', {
            'fields': ('station', 'candidate', 'vote_count')
        }),
        ('معلومات الإدخال', {
            'fields': ('entered_by', 'entered_at', 'updated_at', 'notes')
        }),
    )


# ==================== Barcode Scanning Admin ====================

@admin.register(BarcodeScanSession)
class BarcodeScanSessionAdmin(admin.ModelAdmin):
    """إدارة جلسات مسح الباركود"""
    list_display = ['session_code', 'operator', 'vote_type', 'status', 
                   'total_scans', 'successful_scans', 'failed_scans', 
                   'get_success_rate', 'started_at']
    list_filter = ['vote_type', 'status', 'started_at']
    search_fields = ['session_code', 'operator__username']
    readonly_fields = ['session_code', 'started_at', 'get_success_rate']
    date_hierarchy = 'started_at'
    ordering = ['-started_at']
    
    fieldsets = (
        ('معلومات الجلسة', {
            'fields': ('session_code', 'operator', 'vote_type', 'status')
        }),
        ('التوقيت', {
            'fields': ('started_at', 'completed_at')
        }),
        ('الإحصائيات', {
            'fields': ('total_scans', 'successful_scans', 'failed_scans', 
                      'duplicate_scans', 'get_success_rate')
        }),
        ('ملاحظات', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_success_rate(self, obj):
        """عرض نسبة النجاح"""
        return f"{obj.get_success_rate()}%"
    get_success_rate.short_description = 'نسبة النجاح'
    
    actions = ['mark_as_completed', 'mark_as_cancelled']
    
    @admin.action(description='تحديد كمكتمل')
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'تم تحديد {count} جلسة كمكتملة.')
    
    @admin.action(description='تحديد كملغاة')
    def mark_as_cancelled(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(status='cancelled', completed_at=timezone.now())
        self.message_user(request, f'تم إلغاء {count} جلسة.')


@admin.register(BarcodeScanRecord)
class BarcodeScanRecordAdmin(admin.ModelAdmin):
    """إدارة سجلات مسح الباركود"""
    list_display = ['get_full_station_code', 'center_number', 'station_number', 
                   'vote_type', 'status', 'operator', 'scanned_at']
    list_filter = ['status', 'vote_type', 'is_processed', 'scanned_at']
    search_fields = ['barcode_data', 'center_number', 'station_number', 
                    'polling_center__name', 'polling_station__full_number']
    readonly_fields = ['scanned_at', 'processed_at', 'get_full_station_code']
    date_hierarchy = 'scanned_at'
    ordering = ['-scanned_at']
    list_per_page = 50
    
    fieldsets = (
        ('معلومات المسح', {
            'fields': ('session', 'operator', 'scanned_at')
        }),
        ('بيانات الباركود', {
            'fields': ('barcode_data', 'barcode_type', 'barcode_image')
        }),
        ('البيانات المستخرجة', {
            'fields': ('center_number', 'station_number', 'vote_type', 'scan_date',
                      'get_full_station_code')
        }),
        ('الربط بقاعدة البيانات', {
            'fields': ('polling_center', 'polling_station')
        }),
        ('بيانات الأصوات', {
            'fields': ('vote_data', 'total_votes', 'valid_votes', 'invalid_votes'),
            'classes': ('collapse',)
        }),
        ('الحالة والتحقق', {
            'fields': ('status', 'validation_errors', 'validation_warnings')
        }),
        ('المعالجة', {
            'fields': ('is_processed', 'processed_at', 'processed_by')
        }),
    )
    
    actions = ['mark_as_validated', 'mark_as_processed', 'mark_as_rejected', 'reprocess_scans']
    
    @admin.action(description='تحديد كتم التحقق منه')
    def mark_as_validated(self, request, queryset):
        count = queryset.update(status='validated')
        self.message_user(request, f'تم التحقق من {count} مسح.')
    
    @admin.action(description='تحديد كتمت معالجته')
    def mark_as_processed(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(status='processed', is_processed=True, 
                               processed_at=timezone.now(), processed_by=request.user)
        self.message_user(request, f'تمت معالجة {count} مسح.')
    
    @admin.action(description='تحديد كمرفوض')
    def mark_as_rejected(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f'تم رفض {count} مسح.')
    
    @admin.action(description='إعادة معالجة')
    def reprocess_scans(self, request, queryset):
        count = queryset.update(status='pending', is_processed=False)
        self.message_user(request, f'تمت إعادة {count} مسح للمعالجة.')

